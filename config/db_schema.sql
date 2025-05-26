-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema virtual_wallet_db
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema virtual_wallet_db
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `virtual_wallet_db` ;
USE `virtual_wallet_db` ;

-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`Users`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`Users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(20) NOT NULL,
  `email` VARCHAR(40) NOT NULL,
  `phone_number` VARCHAR(32) NOT NULL,
  `password_hash` VARCHAR(72) NOT NULL,
  `is_admin` TINYINT NOT NULL DEFAULT 0,
  `is_blocked` TINYINT NOT NULL DEFAULT 0,
  `avatar_url` VARCHAR(256) NULL DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  PRIMARY KEY (`id`),
  UNIQUE INDEX `username_UNIQUE` (`username` ASC) VISIBLE,
  UNIQUE INDEX `phone_number_UNIQUE` (`phone_number` ASC) VISIBLE,
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`CurrencyTypes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`CurrencyTypes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `type` VARCHAR(3) NOT NULL,
  `name` VARCHAR(16) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `type_UNIQUE` (`type` ASC) VISIBLE,
  UNIQUE INDEX `name_UNIQUE` (`name` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`Balances`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`Balances` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `currency_id` INT NOT NULL,
  `current_balance` FLOAT NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`id`),
  INDEX `fk_Balances_CurrencyTypes1_idx` (`currency_id` ASC) VISIBLE,
  CONSTRAINT `fk_Balances_CurrencyTypes1`
    FOREIGN KEY (`currency_id`)
    REFERENCES `virtual_wallet_db`.`CurrencyTypes` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`BankCards`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`BankCards` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `balance_id` INT NOT NULL,
  `encrypted_card_info` TEXT NOT NULL,
  `type` ENUM('CREDIT', 'DEBIT') NOT NULL,
  `nickname` VARCHAR(40) NULL DEFAULT NULL,
  `image_url` VARCHAR(256) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_BankCards_Users1_idx` (`user_id` ASC) VISIBLE,
  INDEX `fk_BankCards_Balances1_idx` (`balance_id` ASC) VISIBLE,
  CONSTRAINT `fk_BankCards_Users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `virtual_wallet_db`.`Users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_BankCards_Balances1`
    FOREIGN KEY (`balance_id`)
    REFERENCES `virtual_wallet_db`.`Balances` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`TransactionCategories`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`TransactionCategories` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `name` VARCHAR(40) NOT NULL,
  `image_url` TEXT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_TransactionCategories_Users1_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_TransactionCategories_Users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `virtual_wallet_db`.`Users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`UserContacts`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`UserContacts` (
  `user_id` INT NOT NULL,
  `contact_id` INT NOT NULL,
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


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`Transactions`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`Transactions` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `category_id` INT NOT NULL,
  `name` VARCHAR(32) NULL DEFAULT 'No Name',
  `description` VARCHAR(256) NULL DEFAULT 'No Description',
  `sender_id` INT NOT NULL,
  `receiver_id` INT NOT NULL,
  `amount` FLOAT NOT NULL,
  `currency_id` INT NOT NULL,
  `is_accepted` TINYINT NOT NULL DEFAULT 0,
  `is_recurring` TINYINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  INDEX `fk_Transactions_TransactionCategories1_idx` (`category_id` ASC) VISIBLE,
  INDEX `fk_Transactions_Users1_idx` (`sender_id` ASC) VISIBLE,
  INDEX `fk_Transactions_Users2_idx` (`receiver_id` ASC) VISIBLE,
  INDEX `fk_Transactions_CurrencyTypes1_idx` (`currency_id` ASC) VISIBLE,
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
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Transactions_CurrencyTypes1`
    FOREIGN KEY (`currency_id`)
    REFERENCES `virtual_wallet_db`.`CurrencyTypes` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `virtual_wallet_db`.`Recurring`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `virtual_wallet_db`.`Recurring` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `transaction_id` INT NOT NULL,
  `interval` INT NOT NULL,
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


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
