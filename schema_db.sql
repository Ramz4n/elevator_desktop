-- schema_db.sql
-- Структура таблиц БД vostok_db.
-- Все CREATE TABLE идемпотентны (IF NOT EXISTS) — этот файл безопасно
-- выполнять повторно на уже существующей БД с данными, ничего не удаляется.

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS=0;

CREATE TABLE IF NOT EXISTS `goroda` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Город` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;

CREATE TABLE IF NOT EXISTS `street` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Улица` varchar(100) NOT NULL,
  `id_город` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_город` (`id_город`),
  CONSTRAINT `street_ibfk_1` FOREIGN KEY (`id_город`) REFERENCES `goroda` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;

CREATE TABLE IF NOT EXISTS `uk` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Название` varchar(255) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;

CREATE TABLE IF NOT EXISTS `doma` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Номер` varchar(100) NOT NULL,
  `id_улица` int(11) DEFAULT NULL,
  `id_ук` int(11) DEFAULT NULL,
  `is_active` int(2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_улица` (`id_улица`),
  KEY `id_ук` (`id_ук`),
  CONSTRAINT `doma_ibfk_1` FOREIGN KEY (`id_улица`) REFERENCES `street` (`id`),
  CONSTRAINT `fk_doma_uk` FOREIGN KEY (`id_ук`) REFERENCES `uk` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;

CREATE TABLE IF NOT EXISTS `padik` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Номер` varchar(15) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;

CREATE TABLE IF NOT EXISTS `lifts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_дом` int(11) DEFAULT NULL,
  `id_подъезд` int(11) DEFAULT NULL,
  `Тип_лифта` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_дом` (`id_дом`),
  KEY `id_подъезд` (`id_подъезд`),
  CONSTRAINT `lifts_ibfk_1` FOREIGN KEY (`id_дом`) REFERENCES `doma` (`id`),
  CONSTRAINT `lifts_ibfk_2` FOREIGN KEY (`id_подъезд`) REFERENCES `padik` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;

CREATE TABLE IF NOT EXISTS `workers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ФИО` varchar(100) NOT NULL,
  `Должность` varchar(50) NOT NULL,
  `is_active` tinyint(2) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;

CREATE TABLE IF NOT EXISTS `zayavki` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Номер_заявки` int(11) DEFAULT NULL,
  `Дата_заявки` int(11) DEFAULT NULL,
  `id_диспетчер` int(11) DEFAULT NULL,
  `id_город` int(11) DEFAULT NULL,
  `id_улица` int(11) DEFAULT NULL,
  `id_дом` int(11) DEFAULT NULL,
  `id_подъезд` int(11) DEFAULT NULL,
  `Тип_лифта` varchar(20) DEFAULT NULL,
  `Причина` varchar(50) DEFAULT NULL,
  `Дата_запуска` int(11) DEFAULT NULL,
  `id_механик` int(11) DEFAULT NULL,
  `Комментарий` varchar(255) DEFAULT NULL,
  `id_лифт` int(11) DEFAULT NULL,
  `pc_id` int(2) DEFAULT NULL,
  `id_исполнитель` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_диспетчер` (`id_диспетчер`),
  KEY `id_механик` (`id_механик`),
  KEY `id_лифт` (`id_лифт`),
  KEY `id_город` (`id_город`),
  KEY `id_улица` (`id_улица`),
  KEY `id_дом` (`id_дом`),
  KEY `id_подъезд` (`id_подъезд`),
  KEY `fk_zayavki_workers` (`id_исполнитель`),
  CONSTRAINT `fk_zayavki_workers` FOREIGN KEY (`id_исполнитель`) REFERENCES `workers` (`id`),
  CONSTRAINT `zayavki_ibfk_2` FOREIGN KEY (`id_диспетчер`) REFERENCES `workers` (`id`),
  CONSTRAINT `zayavki_ibfk_3` FOREIGN KEY (`id_механик`) REFERENCES `workers` (`id`),
  CONSTRAINT `zayavki_ibfk_4` FOREIGN KEY (`id_лифт`) REFERENCES `lifts` (`id`),
  CONSTRAINT `zayavki_ibfk_5` FOREIGN KEY (`id_город`) REFERENCES `goroda` (`id`),
  CONSTRAINT `zayavki_ibfk_6` FOREIGN KEY (`id_улица`) REFERENCES `street` (`id`),
  CONSTRAINT `zayavki_ibfk_7` FOREIGN KEY (`id_дом`) REFERENCES `doma` (`id`),
  CONSTRAINT `zayavki_ibfk_8` FOREIGN KEY (`id_подъезд`) REFERENCES `padik` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;

SET FOREIGN_KEY_CHECKS=1;
