import asyncio
import time
from typing import List, Optional

from mapadroid.db.DbWrapper import DbWrapper
from mapadroid.db.helper.PokestopHelper import PokestopHelper
from mapadroid.db.model import SettingsAreaPokestop, SettingsRoutecalc
from mapadroid.geofence.geofenceHelper import GeofenceHelper
from mapadroid.route.RouteManagerBase import RouteManagerBase
from mapadroid.utils.collections import Location
from mapadroid.utils.logging import LoggerEnums, get_logger

logger = get_logger(LoggerEnums.routemanager)


class RouteManagerQuests(RouteManagerBase):
    def __init__(self, db_wrapper: DbWrapper, area: SettingsAreaPokestop, coords: Optional[List[Location]],
                 max_radius: int, max_coords_within_radius: int,
                 geofence_helper: GeofenceHelper, routecalc: SettingsRoutecalc,
                 joinqueue=None, mon_ids_iv: Optional[List[int]] = None):
        RouteManagerBase.__init__(self, db_wrapper=db_wrapper, area=area, coords=coords,
                                  max_radius=max_radius,
                                  max_coords_within_radius=max_coords_within_radius,
                                  geofence_helper=geofence_helper,
                                  routecalc=routecalc, joinqueue=joinqueue, use_s2=False,
                                  mon_ids_iv=mon_ids_iv
                                  )
        self._settings: SettingsAreaPokestop = area
        self._calctype: str = area.route_calc_algorithm
        self.starve_route = False
        self._stoplist: List[Location] = []
        self.init: bool = True if area.init == 1 else False
        self._shutdown_route: bool = False
        self._routecopy: List[Location] = []
        self._tempinit: bool = False

    async def generate_stop_list(self):
        await asyncio.sleep(5)
        # stops = self.db_wrapper.stop_from_db_without_quests(self.geofence_helper)
        # TODO
        stops = []
        self.logger.info('Detected stops without quests: {}', len(stops))
        self.logger.debug('Detected stops without quests: {}', stops)
        self._stoplist: List[Location] = stops

    def _retrieve_latest_priority_queue(self):
        return None

    async def _get_coords_post_init(self):
        async with self.db_wrapper as session, session:
            return await PokestopHelper.get_locations_in_fence(session, self.geofence_helper)

    def _cluster_priority_queue_criteria(self):
        pass

    def _priority_queue_update_interval(self):
        return 0

    async def _recalc_route_workertype(self):
        if self.init:
            await self.recalc_route(self._max_radius, self._max_coords_within_radius, 1, delete_old_route=True,
                              in_memory=False)
        else:
            await self.recalc_route(self._max_radius, self._max_coords_within_radius, 1, delete_old_route=False,
                              in_memory=True)

        self._init_route_queue()

    async def _get_coords_after_finish_route(self) -> bool:
        async with self._manager_mutex:
            if self._shutdown_route:
                self.logger.info('Other worker shutdown - leaving it')
                return False

            if self._start_calc:
                self.logger.info("Another process already calculate the new route")
                return True
            self._start_calc = True
            await self.generate_stop_list()
            if len(self._stoplist) == 0:
                self.logger.info("Dont getting new stops - leaving now.")
                self._shutdown_route = True
                self._restore_original_route()
                self._start_calc = False
                return False
            coords: List[Location] = self._check_unprocessed_stops()
            # remove coords to be ignored from coords
            coords = [coord for coord in coords if coord not in self._coords_to_be_ignored]
            if len(coords) > 0:
                self.logger.info("Getting new coords - recalculating route")
                self._recalc_stop_route(coords)
                self._start_calc = False
            else:
                self.logger.info("Dont getting new stops - leaving now.")
                self._shutdown_route = True
                self._start_calc = False
                self._restore_original_route()
                return False
            return True

    def _restore_original_route(self):
        if not self._tempinit:
            self.logger.info("Restoring original route")
            self._route = self._routecopy.copy()

    def _check_unprocessed_stops(self):
        list_of_stops_to_return: List[Location] = []

        if len(self._stoplist) == 0:
            return list_of_stops_to_return
        else:
            # we only want to add stops that we haven't spun yet
            for stop in self._stoplist:
                if stop not in self._stops_not_processed and stop not in self._get_unprocessed_coords_from_worker():
                    self._stops_not_processed[stop] = 1
                else:
                    self._stops_not_processed[stop] += 1

        for stop, error_count in self._stops_not_processed.items():
            if stop not in self._stoplist:
                self.logger.info("Location {} is no longer in our stoplist and will be ignored", stop)
                self._coords_to_be_ignored.add(stop)
            elif error_count < 4:
                self.logger.info("Found stop not processed yet: {}", stop)
                list_of_stops_to_return.append(stop)
            else:
                self.logger.warning("Stop {} has not been processed thrice in a row, please check your DB", stop)
                self._coords_to_be_ignored.add(stop)

        if len(list_of_stops_to_return) > 0:
            self.logger.info("Found stops not yet processed, retrying those in the next round")
        return list_of_stops_to_return

    async def start_routemanager(self):
        async with self._manager_mutex:
            if not self._is_started:
                self._is_started = True
                self.logger.info("Starting routemanager")

                if self._shutdown_route:
                    self.logger.info('Other worker shutdown - leaving it')
                    return False

                await self.generate_stop_list()
                stops = self._stoplist
                self._prio_queue = None
                self.delay_after_timestamp_prio = None
                self.starve_route = False
                await self._start_check_routepools()

                if self.init:
                    self.logger.info('Starting init mode')
                    self._init_route_queue()
                    self._tempinit = True
                    return True

                if not self._first_started:
                    self.logger.info("First starting quest route - copying original route for later use")
                    self._routecopy = self._route.copy()
                    self._first_started = True
                else:
                    self.logger.info("Restoring original route")
                    self._route = self._routecopy.copy()

                new_stops = list(set(stops) - set(self._route))
                if len(new_stops) > 0:
                    for stop in new_stops:
                        self.logger.info("Stop with coords {} seems new and not in route.", stop)

                if len(stops) == 0:
                    self.logger.info('No unprocessed Stops detected in route - quit worker')
                    self._shutdown_route = True
                    self._restore_original_route()
                    self._route: List[Location] = []
                    return False

                if 0 < len(stops) < len(self._route) \
                        and len(stops) / len(self._route) <= 0.3:
                    # Calculating new route because 70 percent of stops are processed
                    self.logger.info('There are less stops without quest than routepositions - recalc')
                    self._recalc_stop_route(stops)
                elif len(self._route) == 0 and len(stops) > 0:
                    self.logger.warning("Something wrong with area: it contains a lot of new stops - "
                                        "better recalc the route!")
                    self.logger.info("Recalc new route for area")
                    self._recalc_stop_route(stops)
                else:
                    self._init_route_queue()

                self.logger.info('Getting {} positions in route', len(self._route))
                return True
        return True

    def _recalc_stop_route(self, stops):
        self._clear_coords()
        self.add_coords_list(stops)
        self._overwrite_calculation = True
        self._recalc_route_workertype()
        self._init_route_queue()

    def _delete_coord_after_fetch(self) -> bool:
        return True

    def _quit_route(self):
        self.logger.info('Shutdown Route')
        if self._is_started:
            self._is_started = False
            self._round_started_time = None
            if self.init:
                self._first_started = False
            self._restore_original_route()
            self._shutdown_route = False

        # clear not processed stops
        self._stops_not_processed.clear()
        self._coords_to_be_ignored.clear()

    def _check_coords_before_returning(self, lat, lng, origin):
        if self.init:
            self.logger.debug('Init Mode - coord is valid')
            return True
        stop = Location(lat, lng)
        self.logger.info('Checking Stop with ID {}', stop)
        if stop not in self._stoplist and stop not in self._coords_to_be_ignored:
            self.logger.info('Already got this Stop')
            return False
        self.logger.info('Getting new Stop')
        return True

    async def _change_init_mapping(self) -> None:
        self._settings.init = False
        # TODO: Add or merge? Or first fetch the data? Or just toggle using the helper?
        async with self.db_wrapper as session, session:
            await session.merge(self._settings)
