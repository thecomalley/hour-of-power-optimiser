provider "azurerm" {
  features {}
}

locals {
  names = {
    azurerm_storage_account    = "sthopprdaue"
    azurerm_resource_group     = "rg-hop-prd-aue"
    azurerm_service_plan       = "func-hop-prd-aue"
    azurerm_linux_function_app = "asp-hop-prd-aue"
  }
}

resource "azurerm_resource_group" "main" {
  name     = local.names.azurerm_resource_group
  location = "Australia East"
}

resource "azurerm_storage_account" "main" {
  name                     = local.names.azurerm_storage_account
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_service_plan" "main" {
  name                = local.names.azurerm_service_plan
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "main" {
  name                = local.names.azurerm_linux_function_app
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  storage_account_name       = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key
  service_plan_id            = azurerm_service_plan.main.id

  site_config {}
}
