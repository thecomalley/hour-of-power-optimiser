provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "main-resources"
  location = "West Europe"
}

resource "azurerm_storage_account" "main" {
  name                     = "linuxfunctionappsa"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_service_plan" "main" {
  name                = "main-app-service-plan"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "main" {
  name                = "main-linux-function-app"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  storage_account_name = azurerm_storage_account.main.name
  service_plan_id      = azurerm_service_plan.main.id

  builtin_logging_enabled = false

  site_config {
    application_stack {
      python_version = "3.9"
    }
  }

  app_settings {
    
  }
}