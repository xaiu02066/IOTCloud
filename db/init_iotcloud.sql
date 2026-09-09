-- ============================================================
-- 智慧农业环境监控平台 · 元数据数据库初始化脚本
-- 数据库: iotcloud  (MySQL 8 / utf8mb4)
-- 物模型: 智能环境测控仪 (env_ctrl)
-- 设计要点:
--   1) products 表保留 thing_model(JSON) 存完整物模型，前端一次加载；
--      同时用 product_properties / product_services / product_events
--      关系表存关键字段，便于运维 SQL 查询与管理界面展示。
--   2) 告警规则单独建表 alarm_rules。
--   3) 只读型时序数据(温湿度等)走 InfluxDB，不在本库。
-- ============================================================

-- ---------- 删除旧库并重建 ----------
DROP DATABASE IF EXISTS iotcloud;
CREATE DATABASE iotcloud
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
USE iotcloud;

-- ---------- 1. 产品表(含完整物模型 JSON 快照) ----------
CREATE TABLE products (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  product_key   VARCHAR(64)  NOT NULL COMMENT '产品标识',
  product_name  VARCHAR(128) NOT NULL COMMENT '产品名称',
  description   VARCHAR(255) DEFAULT NULL COMMENT '产品定位/描述',
  protocol      VARCHAR(32)  DEFAULT 'MQTT' COMMENT '接入协议',
  thing_model   JSON         DEFAULT NULL COMMENT '完整物模型快照(前端一次加载: 产品/属性/服务/事件)',
  created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_product_key (product_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='产品表(含物模型JSON)';

-- ---------- 2. 设备表 (F4 设备管理) ----------
CREATE TABLE devices (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  device_key  VARCHAR(64)  NOT NULL COMMENT '设备标识/DeviceName',
  device_name VARCHAR(128) NOT NULL COMMENT '设备名称',
  product_id  INT UNSIGNED NOT NULL COMMENT '所属产品ID',
  status      TINYINT      DEFAULT 0 COMMENT '0=离线,1=在线',
  created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
  last_online DATETIME     DEFAULT NULL COMMENT '最近上线时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_device_key (device_key),
  KEY idx_product_id (product_id),
  CONSTRAINT fk_device_product FOREIGN KEY (product_id) REFERENCES products (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备表';

-- ---------- 3. 物模型-属性定义(关系表, 便于查询/展示) ----------
CREATE TABLE product_properties (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  product_id    INT UNSIGNED NOT NULL,
  property_name VARCHAR(128) NOT NULL COMMENT '属性名称',
  identifier    VARCHAR(64)  NOT NULL COMMENT '属性标识符',
  data_type     VARCHAR(32)  NOT NULL COMMENT 'float/bool/int/string',
  unit          VARCHAR(16)  DEFAULT NULL COMMENT '单位',
  access_mode   VARCHAR(8)   NOT NULL DEFAULT 'r' COMMENT 'r=只读, rw=读写',
  description   VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_prop (product_id, identifier),
  KEY idx_product_id (product_id),
  CONSTRAINT fk_prop_product FOREIGN KEY (product_id) REFERENCES products (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='物模型-属性定义';

-- ---------- 4. 物模型-服务定义(关系表) ----------
CREATE TABLE product_services (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  product_id    INT UNSIGNED NOT NULL,
  service_name  VARCHAR(128) NOT NULL COMMENT '服务名称',
  identifier    VARCHAR(64)  NOT NULL COMMENT '服务标识符',
  input_params  JSON         DEFAULT NULL COMMENT '输入参数定义',
  output_params JSON         DEFAULT NULL COMMENT '输出参数定义',
  description   VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_svc (product_id, identifier),
  KEY idx_product_id (product_id),
  CONSTRAINT fk_svc_product FOREIGN KEY (product_id) REFERENCES products (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='物模型-服务定义';

-- ---------- 5. 物模型-事件定义(关系表) ----------
CREATE TABLE product_events (
  id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  product_id        INT UNSIGNED NOT NULL,
  event_name        VARCHAR(128) NOT NULL COMMENT '事件名称',
  identifier        VARCHAR(64)  NOT NULL COMMENT '事件标识符',
  trigger_position  VARCHAR(16)  DEFAULT NULL COMMENT '设备端/平台',
  output_params     JSON         DEFAULT NULL COMMENT '输出参数定义',
  trigger_condition VARCHAR(255) DEFAULT NULL COMMENT '触发条件',
  description       VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_evt (product_id, identifier),
  KEY idx_product_id (product_id),
  CONSTRAINT fk_evt_product FOREIGN KEY (product_id) REFERENCES products (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='物模型-事件定义';

-- ---------- 6. 设备属性当前值/配置(读写型属性持久化) ----------
CREATE TABLE device_property_values (
  id                 INT UNSIGNED NOT NULL AUTO_INCREMENT,
  device_id          INT UNSIGNED NOT NULL,
  property_identifier VARCHAR(64) NOT NULL COMMENT '属性标识符',
  value              TEXT         DEFAULT NULL COMMENT '当前/期望值',
  updated_at         DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_dev_prop (device_id, property_identifier),
  KEY idx_device_id (device_id),
  CONSTRAINT fk_dpv_device FOREIGN KEY (device_id) REFERENCES devices (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备属性当前值/配置(读写型)';

-- ---------- 7. 设备指令下发/回执记录 (F6 设备控制) ----------
CREATE TABLE device_commands (
  id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  device_id         INT UNSIGNED NOT NULL,
  service_identifier VARCHAR(64) NOT NULL COMMENT '服务标识符',
  command_id        VARCHAR(64)  DEFAULT NULL COMMENT '指令关联ID(messageId)',
  input_params      JSON         DEFAULT NULL COMMENT '下发参数',
  status            VARCHAR(16)  DEFAULT 'pending' COMMENT 'pending/success/failed/timeout',
  result            VARCHAR(255) DEFAULT NULL COMMENT '回执结果',
  created_at        DATETIME     DEFAULT CURRENT_TIMESTAMP,
  finished_at       DATETIME     DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_device_id (device_id),
  CONSTRAINT fk_cmd_device FOREIGN KEY (device_id) REFERENCES devices (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备指令下发/回执记录';

-- ---------- 8. 设备事件/告警记录 (F8 触发记录) ----------
CREATE TABLE device_events (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  device_id       INT UNSIGNED NOT NULL,
  event_identifier VARCHAR(64) NOT NULL COMMENT '事件标识符',
  output_data     JSON         DEFAULT NULL COMMENT '输出参数',
  created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_device_id (device_id),
  KEY idx_event_identifier (event_identifier),
  CONSTRAINT fk_evt_device FOREIGN KEY (device_id) REFERENCES devices (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备事件/告警触发记录';

-- ---------- 9. 告警规则表 (F8 规则定义) ----------
CREATE TABLE alarm_rules (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  product_id   INT UNSIGNED NOT NULL COMMENT '所属产品',
  device_id    INT UNSIGNED DEFAULT NULL COMMENT '为空=产品级规则, 适用该产品所有设备, 否则仅对该设备生效',
  rule_name    VARCHAR(128) NOT NULL COMMENT '规则名称',
  metric       VARCHAR(64)  NOT NULL COMMENT '监测属性标识符, 如 air_temperature',
  operator     VARCHAR(8)   NOT NULL COMMENT '>, <, >=, <=, ==, !=',
  threshold    DOUBLE       NOT NULL COMMENT '阈值',
  level        VARCHAR(16)  DEFAULT 'warning' COMMENT 'warning/critical',
  enabled      TINYINT      DEFAULT 1 COMMENT '0=禁用, 1=启用',
  description  VARCHAR(255) DEFAULT NULL,
  created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_product_id (product_id),
  KEY idx_device_id (device_id),
  CONSTRAINT fk_alarm_product FOREIGN KEY (product_id) REFERENCES products (id),
  CONSTRAINT fk_alarm_device  FOREIGN KEY (device_id)  REFERENCES devices (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警规则表';

-- ============================================================
-- 物模型种子数据: 智能环境测控仪 (env_ctrl)
-- ============================================================
INSERT INTO products (product_key, product_name, description, protocol, thing_model)
VALUES (
  'env_ctrl',
  '智能环境测控仪',
  '集数据采集与设备控制于一体的农业物联网终端',
  'MQTT',
  '{
    "product_key": "env_ctrl",
    "product_name": "智能环境测控仪",
    "description": "集数据采集与设备控制于一体的农业物联网终端",
    "protocol": "MQTT",
    "properties": [
      {"identifier":"air_temperature","property_name":"空气温度","data_type":"float","unit":"°C","access_mode":"r","description":"传感器采集上报"},
      {"identifier":"air_humidity","property_name":"空气湿度","data_type":"float","unit":"%RH","access_mode":"r","description":"传感器采集上报"},
      {"identifier":"soil_humidity","property_name":"土壤湿度","data_type":"float","unit":"%","access_mode":"r","description":"传感器采集上报"},
      {"identifier":"fan_status","property_name":"风机状态","data_type":"bool","unit":null,"access_mode":"r","description":"true=运转，false=停止"},
      {"identifier":"temp_threshold","property_name":"温度告警阈值","data_type":"float","unit":"°C","access_mode":"rw","description":"用户设定，设备本地存储"},
      {"identifier":"humid_threshold","property_name":"湿度告警阈值","data_type":"float","unit":"%","access_mode":"rw","description":"用户设定，设备本地存储"}
    ],
    "services": [
      {"identifier":"set_fan","service_name":"风机控制","input_params":{"fan_state":"bool"},"output_params":{"result":"string"},"description":"远程开/关风机"},
      {"identifier":"set_threshold","service_name":"设置告警阈值","input_params":{"temp_max":"float","humid_min":"float"},"output_params":{"result":"string"},"description":"批量修改告警线"}
    ],
    "events": [
      {"identifier":"temp_alarm","event_name":"温度超限告警","trigger_position":"设备端","output_params":{"temperature":"float","threshold":"float","timestamp":"string"},"trigger_condition":"温度 > 本地存储阈值"},
      {"identifier":"dry_alarm","event_name":"土壤湿度低告警","trigger_position":"设备端","output_params":{"humidity":"float","threshold":"float","timestamp":"string"},"trigger_condition":"湿度 < 本地存储阈值"},
      {"identifier":"online","event_name":"设备上线","trigger_position":"平台","output_params":{"timestamp":"string"},"trigger_condition":"设备连接成功"},
      {"identifier":"offline","event_name":"设备下线","trigger_position":"平台","output_params":{"timestamp":"string"},"trigger_condition":"心跳超时"}
    ]
  }'
);

SET @pid = LAST_INSERT_ID();

-- 属性(关系表, 与 JSON 中保持一致)
INSERT INTO product_properties (product_id, property_name, identifier, data_type, unit, access_mode, description) VALUES
 (@pid, '空气温度',     'air_temperature', 'float', '°C', 'r',  '传感器采集上报'),
 (@pid, '空气湿度',     'air_humidity',   'float', '%RH', 'r', '传感器采集上报'),
 (@pid, '土壤湿度',     'soil_humidity',  'float', '%',  'r',  '传感器采集上报'),
 (@pid, '风机状态',     'fan_status',     'bool',  NULL, 'r',  'true=运转，false=停止'),
 (@pid, '温度告警阈值', 'temp_threshold', 'float', '°C', 'rw', '用户设定，设备本地存储'),
 (@pid, '湿度告警阈值', 'humid_threshold', 'float', '%', 'rw', '用户设定，设备本地存储');

-- 服务
INSERT INTO product_services (product_id, service_name, identifier, input_params, output_params, description) VALUES
 (@pid, '风机控制',     'set_fan',       '{"fan_state":"bool"}',                          '{"result":"string"}', '远程开/关风机'),
 (@pid, '设置告警阈值', 'set_threshold', '{"temp_max":"float","humid_min":"float"}',      '{"result":"string"}', '批量修改告警线');

-- 事件
INSERT INTO product_events (product_id, event_name, identifier, trigger_position, output_params, trigger_condition, description) VALUES
 (@pid, '温度超限告警',   'temp_alarm', '设备端', '{"temperature":"float","threshold":"float","timestamp":"string"}', '温度 > 本地存储阈值', NULL),
 (@pid, '土壤湿度低告警', 'dry_alarm',  '设备端', '{"humidity":"float","threshold":"float","timestamp":"string"}',   '湿度 < 本地存储阈值', NULL),
 (@pid, '设备上线',       'online',     '平台',   '{"timestamp":"string"}',                                          '设备连接成功',       NULL),
 (@pid, '设备下线',       'offline',    '平台',   '{"timestamp":"string"}',                                          '心跳超时',           NULL);

-- 告警规则(示例: 产品级规则, 适用于 env_ctrl 下所有设备)
INSERT INTO alarm_rules (product_id, device_id, rule_name, metric, operator, threshold, level, enabled, description) VALUES
 (@pid, NULL, '温度超限告警', 'air_temperature', '>', 35, 'warning', 1, '空气温度高于 35°C 触发'),
 (@pid, NULL, '土壤湿度低告警', 'soil_humidity', '<', 20, 'warning', 1, '土壤湿度低于 20% 触发');
