-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';


-- -----------------------------------------------------
-- Schema virtual_wallet_db
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `virtual_wallet_db` ;
USE `virtual_wallet_db` ;

-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`Currencies`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`Currencies` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(3) NOT NULL,
  `name` VARCHAR(32) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`Users`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`Users` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(20) NOT NULL,
  `email` VARCHAR(40) NOT NULL,
  `phone_number` VARCHAR(32) NOT NULL,
  `password_hash` VARCHAR(72) NOT NULL,
  `is_admin` TINYINT(4) NOT NULL DEFAULT 0,
  `is_blocked` TINYINT(4) NOT NULL DEFAULT 0,
  `is_verified` TINYINT(4) NOT NULL DEFAULT 0,
  `balance` FLOAT NOT NULL DEFAULT 0,
  `currency_id` INT(11) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  `avatar_url` VARCHAR(256) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `username_UNIQUE` (`username` ASC) VISIBLE,
  UNIQUE INDEX `phone_number_UNIQUE` (`phone_number` ASC) VISIBLE,
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE,
  INDEX `fk_Users_Currencies1_idx` (`currency_id` ASC) VISIBLE,
  CONSTRAINT `fk_Users_Currencies1`
    FOREIGN KEY (`currency_id`)
    REFERENCES `virtual_wallet_db`.`Currencies` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`BankCards`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`BankCards` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `user_id` INT(11) NOT NULL,
  `encrypted_card_info` TEXT NOT NULL,
  `type` ENUM('CREDIT', 'DEBIT') NOT NULL,
  `is_deactivated` TINYINT(4) NOT NULL DEFAULT 0,
  `nickname` VARCHAR(40) NULL DEFAULT NULL,
  `image_url` VARCHAR(256) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_BankCards_Users1_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_BankCards_Users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `virtual_wallet_db`.`Users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`TransactionCategories`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`TransactionCategories` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `user_id` INT(11) NOT NULL,
  `name` VARCHAR(40) NOT NULL,
  `image_url` VARCHAR(256) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_TransactionCategories_Users1_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_TransactionCategories_Users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `virtual_wallet_db`.`Users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`Transactions`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`Transactions` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `category_id` INT(11) NOT NULL,
  `name` VARCHAR(32) NOT NULL,
  `description` VARCHAR(256) NOT NULL,
  `sender_id` INT(11) NOT NULL,
  `receiver_id` INT(11) NOT NULL,
  `amount` FLOAT NOT NULL,
  `currency_id` INT(11) NOT NULL,
  `is_accepted` TINYINT(4) NOT NULL DEFAULT 0,
  `is_recurring` TINYINT(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  INDEX `fk_Transactions_TransactionCategories1_idx` (`category_id` ASC) VISIBLE,
  INDEX `fk_Transactions_Users1_idx` (`sender_id` ASC) VISIBLE,
  INDEX `fk_Transactions_Users2_idx` (`receiver_id` ASC) VISIBLE,
  CONSTRAINT `fk_Transactions_TransactionCategories1`
    FOREIGN KEY (`category_id`)
    REFERENCES `virtual_wallet_db`.`TransactionCategories` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Transactions_Users1`
    FOREIGN KEY (`sender_id`)
    REFERENCES `virtual_wallet_db`.`Users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Transactions_Users2`
    FOREIGN KEY (`receiver_id`)
    REFERENCES `virtual_wallet_db`.`Users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`Recurring`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`Recurring` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `transaction_id` INT(11) NOT NULL,
  `interval` INT(11) NOT NULL,
  `interval_type` ENUM('HOURS', 'DAYS') NOT NULL,
  `next_exec_date` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_Recurring_Transactions1_idx` (`transaction_id` ASC) VISIBLE,
  CONSTRAINT `fk_Recurring_Transactions1`
    FOREIGN KEY (`transaction_id`)
    REFERENCES `virtual_wallet_db`.`Transactions` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`UserContacts`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`UserContacts` (
  `user_id` INT(11) NOT NULL,
  `contact_id` INT(11) NOT NULL,
  PRIMARY KEY (`user_id`, `contact_id`),
  INDEX `fk_Users_has_Users_Users2_idx` (`contact_id` ASC) VISIBLE,
  INDEX `fk_Users_has_Users_Users1_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_Users_has_Users_Users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `virtual_wallet_db`.`Users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Users_has_Users_Users2`
    FOREIGN KEY (`contact_id`)
    REFERENCES `virtual_wallet_db`.`Users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
