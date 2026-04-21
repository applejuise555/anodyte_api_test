-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: test_5
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `anodize_log`
--

DROP TABLE IF EXISTS `anodize_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `anodize_log` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `anodize_id` int NOT NULL,
  `ph` decimal(4,2) DEFAULT NULL,
  `density` decimal(6,3) DEFAULT NULL,
  `temperature` decimal(5,2) DEFAULT NULL,
  `recorded_at` datetime NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`log_id`),
  KEY `idx_anodize_time` (`recorded_at`),
  KEY `idx_anodize_fk` (`anodize_id`),
  CONSTRAINT `anodize_log_ibfk_1` FOREIGN KEY (`anodize_id`) REFERENCES `anodize_tank` (`anodize_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `anodize_log`
--

LOCK TABLES `anodize_log` WRITE;
/*!40000 ALTER TABLE `anodize_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `anodize_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `anodize_log_product`
--

DROP TABLE IF EXISTS `anodize_log_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `anodize_log_product` (
  `id` int NOT NULL AUTO_INCREMENT,
  `log_id` int NOT NULL,
  `jig_product_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_alp_log` (`log_id`),
  KEY `idx_alp_product` (`jig_product_id`),
  CONSTRAINT `anodize_log_product_ibfk_1` FOREIGN KEY (`log_id`) REFERENCES `anodize_log` (`log_id`),
  CONSTRAINT `anodize_log_product_ibfk_2` FOREIGN KEY (`jig_product_id`) REFERENCES `jig_product` (`jig_product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `anodize_log_product`
--

LOCK TABLES `anodize_log_product` WRITE;
/*!40000 ALTER TABLE `anodize_log_product` DISABLE KEYS */;
/*!40000 ALTER TABLE `anodize_log_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `anodize_tank`
--

DROP TABLE IF EXISTS `anodize_tank`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `anodize_tank` (
  `anodize_id` int NOT NULL AUTO_INCREMENT,
  `tank_name` varchar(100) COLLATE utf8mb3_bin DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`anodize_id`),
  UNIQUE KEY `tank_name` (`tank_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `anodize_tank`
--

LOCK TABLES `anodize_tank` WRITE;
/*!40000 ALTER TABLE `anodize_tank` DISABLE KEYS */;
/*!40000 ALTER TABLE `anodize_tank` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `color_bath`
--

DROP TABLE IF EXISTS `color_bath`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `color_bath` (
  `color_bath_id` int NOT NULL AUTO_INCREMENT,
  `tank_name` varchar(100) COLLATE utf8mb3_bin DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`color_bath_id`),
  UNIQUE KEY `tank_name` (`tank_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `color_bath`
--

LOCK TABLES `color_bath` WRITE;
/*!40000 ALTER TABLE `color_bath` DISABLE KEYS */;
/*!40000 ALTER TABLE `color_bath` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `color_bath_log`
--

DROP TABLE IF EXISTS `color_bath_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `color_bath_log` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `color_bath_id` int NOT NULL,
  `ph` decimal(4,2) DEFAULT NULL,
  `temperature` decimal(5,2) DEFAULT NULL,
  `recorded_at` datetime NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`log_id`),
  KEY `idx_color_time` (`recorded_at`),
  KEY `idx_color_fk` (`color_bath_id`),
  CONSTRAINT `color_bath_log_ibfk_1` FOREIGN KEY (`color_bath_id`) REFERENCES `color_bath` (`color_bath_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `color_bath_log`
--

LOCK TABLES `color_bath_log` WRITE;
/*!40000 ALTER TABLE `color_bath_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `color_bath_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jig`
--

DROP TABLE IF EXISTS `jig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jig` (
  `id` int NOT NULL AUTO_INCREMENT,
  `jig_code` varchar(20) COLLATE utf8mb3_bin DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `jig_code` (`jig_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jig`
--

LOCK TABLES `jig` WRITE;
/*!40000 ALTER TABLE `jig` DISABLE KEYS */;
/*!40000 ALTER TABLE `jig` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jig_product`
--

DROP TABLE IF EXISTS `jig_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jig_product` (
  `jig_product_id` int NOT NULL AUTO_INCREMENT,
  `jig_id` int NOT NULL,
  `product_code` varchar(50) COLLATE utf8mb3_bin DEFAULT NULL,
  `product_name` varchar(100) COLLATE utf8mb3_bin DEFAULT NULL,
  `color` varchar(50) COLLATE utf8mb3_bin DEFAULT NULL,
  `width` decimal(6,2) DEFAULT NULL,
  `length` decimal(6,2) DEFAULT NULL,
  `height` decimal(6,2) DEFAULT NULL,
  `thickness` decimal(6,2) DEFAULT NULL,
  `depth` decimal(6,2) DEFAULT NULL,
  `outer_diameter` decimal(6,2) DEFAULT NULL,
  `inner_diameter` decimal(6,2) DEFAULT NULL,
  `surface_type` varchar(100) COLLATE utf8mb3_bin DEFAULT NULL,
  `planned_piece` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`jig_product_id`),
  UNIQUE KEY `uniq_jig_product` (`jig_id`,`product_code`),
  KEY `idx_jig_product_fk` (`jig_id`),
  CONSTRAINT `jig_product_ibfk_1` FOREIGN KEY (`jig_id`) REFERENCES `jig` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jig_product`
--

LOCK TABLES `jig_product` WRITE;
/*!40000 ALTER TABLE `jig_product` DISABLE KEYS */;
/*!40000 ALTER TABLE `jig_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jig_usage_log`
--

DROP TABLE IF EXISTS `jig_usage_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jig_usage_log` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `jig_product_id` int NOT NULL,
  `actual_piece` int DEFAULT NULL,
  `recorded_at` datetime NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`log_id`),
  KEY `idx_jig_usage_time` (`recorded_at`),
  KEY `idx_jig_usage_fk` (`jig_product_id`),
  CONSTRAINT `jig_usage_log_ibfk_1` FOREIGN KEY (`jig_product_id`) REFERENCES `jig_product` (`jig_product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jig_usage_log`
--

LOCK TABLES `jig_usage_log` WRITE;
/*!40000 ALTER TABLE `jig_usage_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `jig_usage_log` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-20 10:29:55
