import datetime
import json
import time

from flask import flash, jsonify, redirect, render_template, request, url_for

from mapadroid.db.DbStatsReader import DbStatsReader
from mapadroid.db.DbWrapper import DbWrapper
from mapadroid.db.helper.TrsStatusHelper import TrsStatusHelper
from mapadroid.madmin.functions import (auth_required,
                                        generate_coords_from_geofence,
                                        get_geofences)
from mapadroid.utils.gamemechanicutil import calculate_iv, calculate_mon_level
from mapadroid.utils.geo import get_distance_of_two_points_in_meters
from mapadroid.utils.language import get_mon_name
from mapadroid.utils.logging import LoggerEnums, get_logger
from mapadroid.utils.MappingManager import MappingManager

logger = get_logger(LoggerEnums.madmin)


class MADminStatistics(object):
    def __init__(self, db_wrapper: DbWrapper, args, app, mapping_manager: MappingManager):
        self._db_wrapper: DbWrapper = db_wrapper
        self._db_stats_reader: DbStatsReader = db.stats_reader
        self._args = args
        self._app = app
        self._mapping_manager = mapping_manager
        if self._args.madmin_time == "12":
            self._datetimeformat = '%Y-%m-%d %I:%M:%S %p'
        else:
            self._datetimeformat = '%Y-%m-%d %H:%M:%S'
        self.outdatedays = self._args.outdated_spawnpoints

    def add_route(self):
        routes = [
            ("/statistics", self.statistics),
            ("/statistics_mon", self.statistics_mon),
            ("/statistics_shiny", self.statistics_shiny),
            ("/get_game_stats_shiny", self.game_stats_shiny_v2),
            ("/get_game_stats", self.game_stats),
            ("/get_game_stats_mon", self.game_stats_mon),
            ("/statistics_detection_worker_data", self.statistics_detection_worker_data),
            ("/statistics_detection_worker", self.statistics_detection_worker),
            ("/status", self.status),
            ("/get_status", self.get_status),
            ("/get_spawnpoints_stats", self.get_spawnpoints_stats),
            ("/get_spawnpoints_stats_summary", self.get_spawnpoints_stats_summary),
            ("/statistics_spawns", self.statistics_spawns),
            ("/shiny_stats", self.statistics_shiny),
            ("/delete_spawns", self.delete_spawns),
            ("/convert_spawns", self.convert_spawns),
            ("/spawn_details", self.spawn_details),
            ("/get_spawn_details", self.get_spawn_details),
            ("/delete_spawn", self.delete_spawn),
            ("/convert_spawn", self.convert_spawn),
            ("/delete_unfenced_spawns", self.delete_unfenced_spawns),
            ("/delete_status_entry", self.delete_status_entry),
            ("/reset_status_entry", self.reset_status_entry),
            ("/get_stop_quest_stats", self.get_stop_quest_stats),
            ("/statistics_stop_quest", self.statistics_stop_quest),
            ("/get_noniv_encounters_count", self.get_noniv_encounters_count),
        ]
        for route, view_func in routes:
            self._app.route(route)(view_func)

    def start_modul(self):
        self.add_route()

    def generate_mon_icon_url(self, mon_id, form=None, costume=None, shiny=False):
        base_path = 'https://raw.githubusercontent.com/whitewillem/PogoAssets/resized/no_border'

        form_str = '_00'
        if form is not None and str(form) != '0':
            form_str = '_' + str(form)

        costume_str = ''
        if costume is not None and str(costume) != '0':
            costume_str = '_' + str(costume)

        shiny_str = ''
        if shiny:
            shiny_str = '_shiny'

        return "{}/pokemon_icon_{:03d}{}{}{}.png".format(base_path, mon_id, form_str, costume_str, shiny_str)

    @auth_required
    def statistics(self):
        minutes_usage = request.args.get('minutes_usage')
        if not minutes_usage:
            minutes_usage = 120

        return render_template('statistics/statistics.html', title="MAD Statistics",
                               minutes_usage=minutes_usage,
                               time=self._args.madmin_time,
                               responsive=str(self._args.madmin_noresponsive).lower())

    @auth_required
    def statistics_mon(self):
        minutes_spawn = request.args.get('minutes_spawn')
        if not minutes_spawn:
            minutes_spawn = 120

        return render_template('statistics/mon_statistics.html', title="MAD Mon Statistics",
                               minutes_spawn=minutes_spawn,
                               time=self._args.madmin_time,
                               responsive=str(self._args.madmin_noresponsive).lower())

    @auth_required
    def statistics_shiny(self):
        return render_template('statistics/shiny_statistics.html', title="MAD Shiny Statistics",
                               time=self._args.madmin_time,
                               responsive=str(self._args.madmin_noresponsive).lower())

    @auth_required
    def statistics_stop_quest(self):
        return render_template('statistics/stop_quest_statistics.html', title="MAD Stop/Quest Statistics",
                               time=self._args.madmin_time,
                               responsive=str(self._args.madmin_noresponsive).lower())

    @logger.catch
    @auth_required
    def game_stats(self):
        minutes_usage = request.args.get('minutes_usage', 10)

        # statistics_get_detection_count
        data = self._db_stats_reader.get_detection_count(grouped=False)
        detection = []
        for dat in data:
            detection.append({'worker': str(dat[1]), 'mons': str(dat[2]), 'mons_iv': str(dat[3]),
                              'raids': str(dat[4]), 'quests': str(dat[5])})

        data = self._db_stats_reader.get_location_info()
        location_info = []
        for dat in data:
            location_info.append({'worker': str(dat[0]), 'locations': str(dat[1]), 'locationsok': str(dat[2]),
                                  'locationsnok': str(dat[3]), 'ratio': str(dat[4]), })

        # empty scans
        data = self._db_stats_reader.get_all_empty_scans()
        detection_empty = []
        for dat in data:
            detection_empty.append({'lat': str(dat[1]), 'lng': str(dat[2]), 'worker': str(dat[3]),
                                    'count': str(dat[0]), 'type': str(dat[4]), 'lastscan': str(dat[5]),
                                    'countsuccess': str(dat[6])})

        # Usage
        insta = {}
        usage = []
        idx = 0
        usa = self._db_stats_reader.get_usage_count(minutes_usage)

        for dat in usa:
            if 'CPU-' + dat[4] not in insta:
                insta['CPU-' + dat[4]] = {}
                insta['CPU-' + dat[4]]["axis"] = 1
                insta['CPU-' + dat[4]]["data"] = []
            if 'MEM-' + dat[4] not in insta:
                insta['MEM-' + dat[4]] = {}
                insta['MEM-' + dat[4]]['axis'] = 2
                insta['MEM-' + dat[4]]["data"] = []
            if self._args.stat_gc:
                if 'CO-' + dat[4] not in insta:
                    insta['CO-' + dat[4]] = {}
                    insta['CO-' + dat[4]]['axis'] = 3
                    insta['CO-' + dat[4]]["data"] = []

            insta['CPU-' + dat[4]]['data'].append([dat[3] * 1000, dat[0]])
            insta['MEM-' + dat[4]]['data'].append([dat[3] * 1000, dat[1]])
            if self._args.stat_gc:
                insta['CO-' + dat[4]]['data'].append([dat[3] * 1000, dat[2]])

        for label in insta:
            usage.append(
                {'label': label, 'data': insta[label]['data'], 'yaxis': insta[label]['axis'], 'idx': idx})
            idx += 1

        # Gym
        gym = []
        data = self._db_stats_reader.get_gym_count()
        for dat in data:
            if dat[0] == 'WHITE':
                color = '#999999'
                text = 'Uncontested'
            elif dat[0] == 'BLUE':
                color = '#0051CF'
                text = 'Mystic'
            elif dat[0] == 'RED':
                color = '#FF260E'
                text = 'Valor'
            elif dat[0] == 'YELLOW':
                color = '#FECC23'
                text = 'Instinct'
            gym.append({'label': text, 'data': dat[1], 'color': color})

        stats = {'gym': gym, 'detection_empty': detection_empty, 'usage': usage,
                 'location_info': location_info, 'detection': detection}
        return jsonify(stats)

    @logger.catch
    @auth_required
    def game_stats_mon(self):
        minutes_spawn = request.args.get('minutes_spawn', 10)

        # Spawn
        iv = []
        noniv = []
        sumg = []
        sumup = {}

        data = self._db_stats_reader.get_pokemon_count(minutes_spawn)
        for dat in data:
            if dat[2] == 1:
                iv.append([(self.utc2local(dat[0]) * 1000), dat[1]])
            else:
                noniv.append([(self.utc2local(dat[0]) * 1000), dat[1]])

            if (self.utc2local(dat[0]) * 1000) in sumup:
                sumup[(self.utc2local(dat[0]) * 1000)] += dat[1]
            else:
                sumup[(self.utc2local(dat[0]) * 1000)] = dat[1]

        for dat in sumup:
            sumg.append([dat, sumup[dat]])

        spawn = {'iv': iv, 'noniv': noniv, 'sum': sumg}

        # good_spawns avg
        good_spawns = []
        data = self._db_stats_reader.get_best_pokemon_spawns()
        if data is not None:
            for dat in data:
                mon_img = self.generate_mon_icon_url(dat[1], dat[8], dat[9])
                mon_name = get_mon_name(dat[1])
                if self._args.db_method == "rm":
                    lvl = calculate_mon_level(dat[6])
                else:
                    lvl = dat[6]
                good_spawns.append({'id': dat[1], 'iv': round(calculate_iv(dat[3], dat[4], dat[5]), 0),
                                    'lvl': lvl, 'cp': dat[7], 'img': mon_img,
                                    'name': mon_name,
                                    'periode': datetime.datetime.fromtimestamp
                                    (self.utc2local(dat[2])).strftime(self._datetimeformat)})

        stats = {'spawn': spawn, 'good_spawns': good_spawns}
        return jsonify(stats)

    @logger.catch
    @auth_required
    def game_stats_shiny_v2(self):
        logger.debug2('game_stats_shiny_v2')
        timestamp_from = request.args.get('from', None)
        if (timestamp_from):
            timestamp_from = self.local2utc(int(timestamp_from))
            logger.debug2('using timestamp_from: {}', timestamp_from)

        timestamp_to = request.args.get('to', None)
        if (timestamp_to):
            timestamp_to = self.local2utc(int(timestamp_to))
            logger.debug2('using timestamp_to: {}', timestamp_to)

        tmp_perworker_v2 = {}
        data = self._db_stats_reader.get_shiny_stats_v2(timestamp_from, timestamp_to)
        found_shiny_mon_id = []
        shiny_count = {}
        mon_names = {}
        tmp_perhour_v2 = {}

        if data is None or len(data) == 0:
            return jsonify({'empty': True})

        shiny_stats_v2 = []
        for dat in data:
            mon = "%03d" % dat[0]
            mon_img = self.generate_mon_icon_url(dat[0], dat[1])
            mon_name = get_mon_name(dat[0])
            mon_names[dat[0]] = mon_name
            found_shiny_mon_id.append(
                mon)  # append everything now, we will set() it later to remove duplicates
            if dat[8] not in tmp_perworker_v2:
                tmp_perworker_v2[dat[8]] = 0
            tmp_perworker_v2[dat[8]] += 1

            if dat[0] not in shiny_count:
                shiny_count[dat[0]] = {}
            if dat[1] not in shiny_count[dat[0]]:
                shiny_count[dat[0]][dat[1]] = 0
            shiny_count[dat[0]][dat[1]] += 1

            # there is later strftime which converts to local time too, can't use utc2local - it will do double shift
            timestamp = datetime.datetime.fromtimestamp(dat[7])

            if timestamp.hour in tmp_perhour_v2:
                tmp_perhour_v2[timestamp.hour] += 1
            else:
                tmp_perhour_v2[timestamp.hour] = 1

            shiny_stats_v2.append({'img': mon_img, 'name': mon_name, 'worker': dat[8], 'lat': dat[2],
                                   'lat_5': "{:.5f}".format(dat[2]), 'lng_5': "{:.5f}".format(dat[3]),
                                   'lng': dat[3], 'timestamp': timestamp.strftime(self._datetimeformat),
                                   'form': dat[1], 'mon_id': dat[0], 'encounter_id': str(dat[9])})

        global_shiny_stats_v2 = []
        data = self._db_stats_reader.get_shiny_stats_global_v2(set(found_shiny_mon_id), timestamp_from,
                                                               timestamp_to)
        for dat in data:
            if dat[1] in shiny_count and dat[2] in shiny_count[dat[1]]:
                odds = round(dat[0] / shiny_count[dat[1]][dat[2]], 0)
                mon = "%03d" % dat[1]
                mon_img = self.generate_mon_icon_url(dat[1], dat[2])
                global_shiny_stats_v2.append({'name': mon_names[dat[1]], 'count': dat[0], 'img': mon_img,
                                              'shiny': shiny_count[dat[1]][dat[2]], 'odds': odds,
                                              'mon_id': dat[1], 'form': dat[2], 'gender': dat[3],
                                              'costume': dat[4]})

        shiny_stats_perworker_v2 = []
        for worker in tmp_perworker_v2:
            shiny_stats_perworker_v2.append({'name': worker, 'count': tmp_perworker_v2[worker]})

        shiny_stats_perhour_v2 = []
        for hour in tmp_perhour_v2:
            shiny_stats_perhour_v2.append([hour, tmp_perhour_v2[hour]])

        stats = {'empty': False, 'shiny_statistics': shiny_stats_v2,
                 'global_shiny_statistics': global_shiny_stats_v2, 'per_worker': shiny_stats_perworker_v2,
                 'per_hour': shiny_stats_perhour_v2}
        return jsonify(stats)

    def utc2local(self, ts):
        utc = datetime.datetime.utcnow()
        now = datetime.datetime.now()
        offset = time.mktime(now.timetuple()) - time.mktime(utc.timetuple())
        return float(ts) + offset

    def local2utc(self, ts):
        utc = datetime.datetime.utcnow()
        now = datetime.datetime.now()
        offset = time.mktime(now.timetuple()) - time.mktime(utc.timetuple())
        return float(ts) - offset

    @auth_required
    def statistics_detection_worker_data(self):
        minutes = request.args.get('minutes', 120)
        worker = request.args.get('worker')

        # spawns
        mon = []
        mon_iv = []
        raid = []
        quest = []
        usage = []

        data = self._db_stats_reader.get_detection_count(minutes=minutes, worker=worker)
        for dat in data:
            mon.append([dat[0] * 1000, int(dat[2])])
            mon_iv.append([dat[0] * 1000, int(dat[3])])
            raid.append([dat[0] * 1000, int(dat[4])])
            quest.append([dat[0] * 1000, int(dat[5])])

        usage.append({'label': 'Mon', 'data': mon})
        usage.append({'label': 'Mon_IV', 'data': mon_iv})
        usage.append({'label': 'Raid', 'data': raid})
        usage.append({'label': 'Quest', 'data': quest})

        # locations avg
        locations_avg = []

        data = self._db_stats_reader.get_avg_data_time(minutes=minutes, worker=worker)
        for dat in data:
            dtime = datetime.datetime.fromtimestamp(dat[0]).strftime(self._datetimeformat)
            locations_avg.append({'dtime': dtime, 'ok_locations': dat[3], 'avg_datareceive': float(dat[4]),
                                  'transporttype': dat[1], 'type': dat[5]})

        # locations
        ok = []
        nok = []
        sumloc = []
        locations = []
        data = self._db_stats_reader.get_locations(minutes=minutes, worker=worker)
        for dat in data:
            ok.append([dat[0] * 1000, int(dat[3])])
            nok.append([dat[0] * 1000, int(dat[4])])
            sumloc.append([dat[0] * 1000, int(dat[2])])

        locations.append({'label': 'Locations', 'data': sumloc})
        locations.append({'label': 'Locations_ok', 'data': ok})
        locations.append({'label': 'Locations_nok', 'data': nok})

        # dataratio
        loctionratio = []
        data = self._db_stats_reader.get_locations_dataratio(minutes=minutes, worker=worker)
        if len(data) > 0:
            for dat in data:
                loctionratio.append({'label': dat[3], 'data': dat[2]})
        else:
            loctionratio.append({'label': '', 'data': 0})

        # all spaws
        all_spawns = []
        data = self._db_stats_reader.get_detection_count(grouped=False, worker=worker)
        all_spawns.append({'type': 'Mon', 'amount': int(data[0][2])})
        all_spawns.append({'type': 'Mon_IV', 'amount': int(data[0][3])})
        all_spawns.append({'type': 'Raid', 'amount': int(data[0][4])})
        all_spawns.append({'type': 'Quest', 'amount': int(data[0][5])})

        # location raw
        location_raw = []
        last_lat = 0
        last_lng = 0
        distance = 0
        data = self._db_stats_reader.get_location_raw(minutes=minutes, worker=worker)
        for dat in data:
            if last_lat != 0 and last_lng != 0:
                distance = round(get_distance_of_two_points_in_meters(last_lat, last_lng, dat[1], dat[2]), 2)
                last_lat = dat[1]
                last_lng = dat[2]
            if last_lat == 0 and last_lng == 0:
                last_lat = dat[1]
                last_lng = dat[2]
            if dat[1] == 0 and dat[2] == 0:
                distance = ''

            location_raw.append(
                {'lat': dat[1], 'lng': dat[2], 'distance': distance, 'type': dat[3], 'data': dat[4],
                 'fix_ts': datetime.datetime.fromtimestamp(dat[5]).strftime(self._datetimeformat),
                 'data_ts': datetime.datetime.fromtimestamp(dat[6]).strftime(self._datetimeformat),
                 'transporttype': dat[8]})

        workerstats = {'avg': locations_avg, 'receiving': usage, 'locations': locations,
                       'ratio': loctionratio, 'allspawns': all_spawns,
                       'location_raw': location_raw}
        return jsonify(workerstats)

    @auth_required
    def statistics_detection_worker(self):
        minutes = request.args.get('minutes', 120)
        worker = request.args.get('worker')

        return render_template('statistics_worker.html', title="MAD Worker Statistics", minutes=minutes,
                               time=self._args.madmin_time, worker=worker,
                               responsive=str(self._args.madmin_noresponsive).lower())

    @auth_required
    def status(self):
        return render_template('status.html', responsive=str(self._args.madmin_noresponsive).lower(),
                               title="Worker status")

    @auth_required
    def get_status(self):
        return jsonify(self._db.download_status())

    @auth_required
    @logger.catch()
    async def get_spawnpoints_stats(self):

        geofence_type = request.args.get('type', 'mon_mitm')
        geofence_id = int(request.args.get('fence', -1))
        if geofence_type not in ['idle', 'iv_mitm', 'mon_mitm', 'pokestops', 'raids_mitm']:
            stats = {'spawnpoints': []}
            return jsonify(stats)

        coords = []
        known = {}
        unknown = {}
        processed_fences = []
        events = []
        eventidhelper = {}

        if geofence_id != -1:
            possible_fences = await get_geofences(self._mapping_manager, self._db_wrapper, area_id_req=geofence_id)
        else:
            possible_fences = await get_geofences(self._mapping_manager, self._db_wrapper, fence_type=geofence_type)

        for possible_fence in possible_fences:
            mode = possible_fences[possible_fence]['mode']
            area_id = possible_fences[possible_fence]['area_id']
            subfenceindex: int = 0

            for subfence in possible_fences[possible_fence]['include']:
                if subfence in processed_fences:
                    continue
                processed_fences.append(subfence)
                fence = await generate_coords_from_geofence(self._mapping_manager, self._db_wrapper, subfence)
                known.clear()
                unknown.clear()
                events.clear()

                data = json.loads(
                    self._db.download_spawns(
                        fence=fence
                    )
                )

                for spawnid in data:
                    eventname: str = data[str(spawnid)]["event"]
                    eventid: str = data[str(spawnid)]["eventid"]
                    if eventname not in known:
                        known[eventname] = []
                    if eventname not in unknown:
                        unknown[eventname] = []
                    if eventname not in events:
                        events.append(eventname)
                        eventidhelper[eventname] = eventid

                    if data[str(spawnid)]["endtime"] is None:
                        unknown[eventname].append(spawnid)
                    else:
                        known[eventname].append(spawnid)

                for event in events:
                    today: int = 0
                    outdate: int = 0

                    if event == "DEFAULT":
                        outdate = self.get_spawn_details_helper(areaid=area_id, eventid=eventidhelper[event],
                                                                olderthanxdays=self.outdatedays, sumonly=True,
                                                                index=subfenceindex)
                    else:
                        today = self.get_spawn_details_helper(areaid=area_id, eventid=eventidhelper[event],
                                                              todayonly=True, sumonly=True, index=subfenceindex)

                    coords.append({'fence': subfence, 'known': len(known[event]), 'unknown': len(unknown[event]),
                                   'sum': len(known[event]) + len(unknown[event]), 'event': event, 'mode': mode,
                                   'area_id': area_id, 'eventid': eventidhelper[event],
                                   'todayspawns': today, 'outdatedspawns': outdate, 'index': subfenceindex
                                   })

                subfenceindex += 1

        stats = {'spawnpoints': coords}
        return jsonify(stats)

    @logger.catch()
    @auth_required
    async def get_stop_quest_stats(self):
        stats = []
        stats_process = []
        processed_fences = []
        possible_fences = await get_geofences(self._mapping_manager, db_wrapper=self._db_wrapper,
                                              fence_type="pokestops")
        wanted_fences = []
        if self._args.quest_stats_fences != "":
            wanted_fences = [item.lower().replace(" ", "") for item in self._args.quest_stats_fences.split(",")]
        for possible_fence in possible_fences:
            subfenceindex: int = 0

            for subfence in possible_fences[possible_fence]['include']:
                if subfence in processed_fences:
                    continue

                if len(wanted_fences) > 0:
                    if str(subfence).lower() not in wanted_fences:
                        continue

                processed_fences.append(subfence)
                fence = await generate_coords_from_geofence(self._mapping_manager, self._db_wrapper, subfence)

                stops = len(self._db.stops_from_db(fence=fence))
                quests = len(self._db.quests_from_db(fence=fence))

                processed: int = 0
                if int(stops) > 0:
                    processed: int = int(quests) * 100 / int(stops)
                info = {
                    "fence": str(subfence),
                    'stops': int(stops),
                    'quests': int(quests),
                    'processed': str(int(processed)) + " %"
                }
                stats_process.append(info)

                subfenceindex += 1

        # Quest
        quest: list = []
        quest_db = self._db_stats_reader.get_quests_count(1)
        for ts, count in quest_db:
            quest_raw = (int(ts * 1000), count)
            quest.append(quest_raw)

        # Stop
        stop = []
        data = self._db_stats_reader.get_stop_quest()
        for dat in data:
            stop.append({'label': dat[0], 'data': dat[1]})

        stats = {'stop_quest_stats': stats_process, 'quest': quest, 'stop': stop}
        return jsonify(stats)

    @auth_required
    @logger.catch()
    def delete_status_entry(self):
        deviceid = request.args.get('deviceid', None)
        self._db.delete_status_entry(deviceid)
        return jsonify({'status': 'success'})

    @auth_required
    @logger.catch()
    async def reset_status_entry(self):
        deviceid = request.args.get('deviceid', None)
        save_data = {
            'device_id': deviceid,
            'globalrebootcount': 0,
            'globalrestartcount': 0,
            'lastPogoRestart': 0,
            'lastPogoReboot': 0,

        }
        await TrsStatusHelper.reset_status(session, instance_id, device_id=deviceid)
        self._db.save_status(save_data)
        return jsonify({'status': 'success'})

    @auth_required
    @logger.catch()
    def delete_spawns(self):
        area_id = request.args.get('id', None)
        event_id = request.args.get('eventid', None)
        olderthanxdays = request.args.get('olderthanxdays', None)
        index = request.args.get('index', 0)
        if self._db.check_if_event_is_active(event_id) and olderthanxdays is None:
            return jsonify({'status': 'event'})
        if area_id is not None and event_id is not None:
            self._db.delete_spawnpoints(self.get_spawnpoints_from_id(area_id, event_id, olderthanxdays=olderthanxdays,
                                                                     index=index))
        if olderthanxdays is not None:
            flash('Successfully deleted outdated spawnpoints')
            return redirect(url_for('statistics_spawns'), code=302)
        return jsonify({'status': 'success'})

    @auth_required
    @logger.catch()
    def convert_spawns(self):
        area_id = request.args.get('id', None)
        event_id = request.args.get('eventid', None)
        todayonly = request.args.get('todayonly', False)
        index = request.args.get('index', 0)
        if self._db.check_if_event_is_active(event_id):
            if todayonly:
                flash('Cannot convert spawnpoints during an event')
                return redirect(url_for('statistics_spawns'), code=302)
            return jsonify({'status': 'event'})
        if area_id is not None and event_id is not None:
            self._db.convert_spawnpoints(self.get_spawnpoints_from_id(area_id, event_id, todayonly=todayonly,
                                                                      index=index))
        if todayonly:
            flash('Successfully converted spawnpoints')
            return redirect(url_for('statistics_spawns'), code=302)
        return jsonify({'status': 'success'})

    @auth_required
    @logger.catch()
    def delete_spawn(self):
        spawn_id = request.args.get('id', None)
        area_id = request.args.get('area_id', None)
        event_id = request.args.get('event_id', None)
        event = request.args.get('event', None)
        if self._db.check_if_event_is_active(event_id):
            flash('Event is still active - cannot delete this spawnpoint now.')
            return redirect(url_for('spawn_details', id=area_id, eventid=event_id, event=event), code=302)
        if spawn_id is not None:
            self._db.delete_spawnpoint(spawn_id)
        return redirect(url_for('spawn_details', id=area_id, eventid=event_id, event=event), code=302)

    @auth_required
    @logger.catch()
    def convert_spawn(self):
        spawn_id = request.args.get('id', None)
        area_id = request.args.get('area_id', None)
        event_id = request.args.get('event_id', None)
        event = request.args.get('event', None)
        # TODO: GODDAMN... just fetch the event and check the datetime instance...
        if self._db.check_if_event_is_active(event_id):
            flash('Event is still active - cannot convert this spawnpoint now.')
            return redirect(url_for('spawn_details', id=area_id, eventid=event_id, event=event), code=302)
        if spawn_id is not None:
            self._db.convert_spawnpoint(spawn_id)
        return redirect(url_for('spawn_details', id=area_id, eventid=event_id, event=event), code=302)

    @auth_required
    @logger.catch()
    async def get_spawnpoints_from_id(self, spawn_id, eventid, todayonly=False, olderthanxdays=None, index=0):
        spawns = []
        possible_fences = await get_geofences(self._mapping_manager, self._db_wrapper, area_id_req=spawn_id)
        fence = await generate_coords_from_geofence(self._mapping_manager, self._db_wrapper,
                                              str(list(possible_fences[int(spawn_id)]['include'].keys())[int(index)]))

        data = json.loads(
            self._db.download_spawns(
                fence=str(fence),
                eventid=int(eventid),
                todayonly=bool(todayonly),
                olderthanxdays=olderthanxdays
            )
        )

        for spawnid in data:
            spawns.append(spawnid)
        return spawns

    @auth_required
    def statistics_spawns(self):
        return render_template('statistics/spawn_statistics.html', title="MAD Spawnpoint Statistics",
                               time=self._args.madmin_time,
                               responsive=str(self._args.madmin_noresponsive).lower())

    @auth_required
    def get_spawn_details(self):

        area_id = request.args.get('area_id', None)
        event_id = request.args.get('event_id', None)
        mode = request.args.get('mode', None)
        index = request.args.get('index', 0)
        olderthanxdays = None
        todayonly = False

        if str(mode) == "OLD":
            olderthanxdays = self.outdatedays
        elif str(mode) == "ALL":
            olderthanxdays = None
            todayonly = False
        else:
            todayonly = True

        return jsonify(self.get_spawn_details_helper(areaid=area_id, eventid=event_id, olderthanxdays=olderthanxdays,
                                                     todayonly=todayonly, index=index))

    async def get_spawn_details_helper(self, areaid, eventid, todayonly=False, olderthanxdays=None, sumonly=False, index=0):
        active_spawns: list = []
        possible_fences = await get_geofences(self._mapping_manager, self._db_wrapper, area_id_req=areaid)
        fence = await generate_coords_from_geofence(self._mapping_manager, self._db_wrapper,
                                              str(list(possible_fences[int(areaid)]['include'].keys())[int(index)]))
        data = json.loads(
            self._db.download_spawns(
                fence=str(fence),
                eventid=int(eventid),
                todayonly=bool(todayonly),
                olderthanxdays=olderthanxdays
            )
        )

        if sumonly:
            return len(data)
        for spawn in data:
            sp = data[spawn]
            active_spawns.append({'id': sp['id'], 'lat': sp['lat'], 'lon': sp['lon'],
                                  'lastscan': sp['lastscan'],
                                  'lastnonscan': sp['lastnonscan']})

        return active_spawns

    @auth_required
    def spawn_details(self):
        area_id = request.args.get('id', None)
        event_id = request.args.get('eventid', None)
        event = request.args.get('event', None)
        mode = request.args.get('mode', "OLD")
        index = request.args.get('index', 0)
        return render_template('statistics/spawn_details.html', title="MAD Spawnpoint Details",
                               time=self._args.madmin_time,
                               responsive=str(self._args.madmin_noresponsive).lower(),
                               areaid=area_id, eventid=event_id, event=event, mode=mode,
                               olderthanxdays=self.outdatedays, index=index)

    @auth_required
    def delete_unfenced_spawns(self):
        processed_fences = []
        spawns = []
        possible_fences = await get_geofences(self._mapping_manager, self._db_wrapper)
        for possible_fence in possible_fences:
            for subfence in possible_fences[possible_fence]['include']:
                if subfence in processed_fences:
                    continue
                processed_fences.append(subfence)
                fence = await generate_coords_from_geofence(self._mapping_manager, self._db_wrapper, subfence)
                data = json.loads(
                    self._db.download_spawns(
                        fence=fence
                    )
                )
                for spawnid in data:
                    spawns.append(spawnid)

        self._db.delete_spawnpoints([x for x in self._db.get_all_spawnpoints() if x not in spawns])

        return jsonify({'status': 'success'})

    @auth_required
    @logger.catch()
    async def get_spawnpoints_stats_summary(self):
        possible_fences = await get_geofences(self._mapping_manager, self._db_wrapper)
        events = self._db.get_events()
        spawnpoints_total = self._db_stats_reader.get_all_spawnpoints_count()
        stats = {'fences': possible_fences, 'events': events, 'spawnpoints_count': spawnpoints_total}
        return jsonify(stats)

    @logger.catch()
    @auth_required
    def get_noniv_encounters_count(self):
        minutes_spawn = request.args.get('minutes_spawn', 240)
        data = self._db_stats_reader.get_noniv_encounters_count(minutes_spawn)
        stats = {'data': data}
        return jsonify(stats)
