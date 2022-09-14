# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: stats_handler/stats_handler.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from mapadroid.grpc.compiled.shared import Ack_pb2 as shared_dot_Ack__pb2
from mapadroid.grpc.compiled.shared import \
    Location_pb2 as shared_dot_Location__pb2
from mapadroid.grpc.compiled.shared import \
    MonSeenTypes_pb2 as shared_dot_MonSeenTypes__pb2
from mapadroid.grpc.compiled.shared import \
    PositionType_pb2 as shared_dot_PositionType__pb2
from mapadroid.grpc.compiled.shared import \
    TransportType_pb2 as shared_dot_TransportType__pb2
from mapadroid.grpc.compiled.shared import Worker_pb2 as shared_dot_Worker__pb2

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n!stats_handler/stats_handler.proto\x12\x17mapadroid.stats_handler\x1a\x15shared/Location.proto\x1a\x10shared/Ack.proto\x1a\x19shared/PositionType.proto\x1a\x1ashared/TransportType.proto\x1a\x19shared/MonSeenTypes.proto\x1a\x13shared/Worker.proto\"\xd9\x03\n\x05Stats\x12-\n\x06worker\x18\x01 \x01(\x0b\x32\x18.mapadroid.shared.WorkerH\x01\x88\x01\x01\x12\x16\n\ttimestamp\x18\x02 \x01(\x04H\x02\x88\x01\x01\x12:\n\twild_mons\x18\x03 \x01(\x0b\x32%.mapadroid.stats_handler.StatsWildMonH\x00\x12\x35\n\x06mon_iv\x18\x04 \x01(\x0b\x32#.mapadroid.stats_handler.StatsMonIvH\x00\x12\x34\n\x05quest\x18\x05 \x01(\x0b\x32#.mapadroid.stats_handler.StatsQuestH\x00\x12\x32\n\x04raid\x18\x06 \x01(\x0b\x32\".mapadroid.stats_handler.StatsRaidH\x00\x12\x43\n\rlocation_data\x18\x07 \x01(\x0b\x32*.mapadroid.stats_handler.StatsLocationDataH\x00\x12;\n\tseen_type\x18\x08 \x01(\x0b\x32&.mapadroid.stats_handler.StatsSeenTypeH\x00\x42\x11\n\x0f\x64\x61ta_to_collectB\t\n\x07_workerB\x0c\n\n_timestamp\"%\n\x0cStatsWildMon\x12\x15\n\rencounter_ids\x18\x01 \x03(\x04\"4\n\nStatsMonIv\x12\x14\n\x0c\x65ncounter_id\x18\x01 \x01(\x04\x12\x10\n\x08is_shiny\x18\x02 \x01(\x08\"\x0c\n\nStatsQuest\"\x1b\n\tStatsRaid\x12\x0e\n\x06\x61mount\x18\x01 \x01(\r\"\x93\x02\n\x11StatsLocationData\x12\x31\n\x08location\x18\x01 \x01(\x0b\x32\x1a.mapadroid.shared.LocationH\x00\x88\x01\x01\x12\x0f\n\x07success\x18\x02 \x01(\x08\x12\x15\n\rfix_timestamp\x18\x03 \x01(\x04\x12\x16\n\x0e\x64\x61ta_timestamp\x18\x04 \x01(\x04\x12\x35\n\rposition_type\x18\x05 \x01(\x0e\x32\x1e.mapadroid.shared.PositionType\x12\x0e\n\x06walker\x18\x06 \x01(\t\x12\x37\n\x0etransport_type\x18\x07 \x01(\x0e\x32\x1f.mapadroid.shared.TransportTypeB\x0b\n\t_location\"a\n\rStatsSeenType\x12\x15\n\rencounter_ids\x18\x01 \x03(\x04\x12\x39\n\x11type_of_detection\x18\x02 \x01(\x0e\x32\x1e.mapadroid.shared.MonSeenTypes2U\n\x0cStatsHandler\x12\x45\n\x0cStatsCollect\x12\x1e.mapadroid.stats_handler.Stats\x1a\x15.mapadroid.shared.Ackb\x06proto3')



_STATS = DESCRIPTOR.message_types_by_name['Stats']
_STATSWILDMON = DESCRIPTOR.message_types_by_name['StatsWildMon']
_STATSMONIV = DESCRIPTOR.message_types_by_name['StatsMonIv']
_STATSQUEST = DESCRIPTOR.message_types_by_name['StatsQuest']
_STATSRAID = DESCRIPTOR.message_types_by_name['StatsRaid']
_STATSLOCATIONDATA = DESCRIPTOR.message_types_by_name['StatsLocationData']
_STATSSEENTYPE = DESCRIPTOR.message_types_by_name['StatsSeenType']
Stats = _reflection.GeneratedProtocolMessageType('Stats', (_message.Message,), {
  'DESCRIPTOR' : _STATS,
  '__module__' : 'stats_handler.stats_handler_pb2'
  # @@protoc_insertion_point(class_scope:mapadroid.stats_handler.Stats)
  })
_sym_db.RegisterMessage(Stats)

StatsWildMon = _reflection.GeneratedProtocolMessageType('StatsWildMon', (_message.Message,), {
  'DESCRIPTOR' : _STATSWILDMON,
  '__module__' : 'stats_handler.stats_handler_pb2'
  # @@protoc_insertion_point(class_scope:mapadroid.stats_handler.StatsWildMon)
  })
_sym_db.RegisterMessage(StatsWildMon)

StatsMonIv = _reflection.GeneratedProtocolMessageType('StatsMonIv', (_message.Message,), {
  'DESCRIPTOR' : _STATSMONIV,
  '__module__' : 'stats_handler.stats_handler_pb2'
  # @@protoc_insertion_point(class_scope:mapadroid.stats_handler.StatsMonIv)
  })
_sym_db.RegisterMessage(StatsMonIv)

StatsQuest = _reflection.GeneratedProtocolMessageType('StatsQuest', (_message.Message,), {
  'DESCRIPTOR' : _STATSQUEST,
  '__module__' : 'stats_handler.stats_handler_pb2'
  # @@protoc_insertion_point(class_scope:mapadroid.stats_handler.StatsQuest)
  })
_sym_db.RegisterMessage(StatsQuest)

StatsRaid = _reflection.GeneratedProtocolMessageType('StatsRaid', (_message.Message,), {
  'DESCRIPTOR' : _STATSRAID,
  '__module__' : 'stats_handler.stats_handler_pb2'
  # @@protoc_insertion_point(class_scope:mapadroid.stats_handler.StatsRaid)
  })
_sym_db.RegisterMessage(StatsRaid)

StatsLocationData = _reflection.GeneratedProtocolMessageType('StatsLocationData', (_message.Message,), {
  'DESCRIPTOR' : _STATSLOCATIONDATA,
  '__module__' : 'stats_handler.stats_handler_pb2'
  # @@protoc_insertion_point(class_scope:mapadroid.stats_handler.StatsLocationData)
  })
_sym_db.RegisterMessage(StatsLocationData)

StatsSeenType = _reflection.GeneratedProtocolMessageType('StatsSeenType', (_message.Message,), {
  'DESCRIPTOR' : _STATSSEENTYPE,
  '__module__' : 'stats_handler.stats_handler_pb2'
  # @@protoc_insertion_point(class_scope:mapadroid.stats_handler.StatsSeenType)
  })
_sym_db.RegisterMessage(StatsSeenType)

_STATSHANDLER = DESCRIPTOR.services_by_name['StatsHandler']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _STATS._serialized_start=207
  _STATS._serialized_end=680
  _STATSWILDMON._serialized_start=682
  _STATSWILDMON._serialized_end=719
  _STATSMONIV._serialized_start=721
  _STATSMONIV._serialized_end=773
  _STATSQUEST._serialized_start=775
  _STATSQUEST._serialized_end=787
  _STATSRAID._serialized_start=789
  _STATSRAID._serialized_end=816
  _STATSLOCATIONDATA._serialized_start=819
  _STATSLOCATIONDATA._serialized_end=1094
  _STATSSEENTYPE._serialized_start=1096
  _STATSSEENTYPE._serialized_end=1193
  _STATSHANDLER._serialized_start=1195
  _STATSHANDLER._serialized_end=1280
# @@protoc_insertion_point(module_scope)
