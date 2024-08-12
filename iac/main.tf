resource "azurerm_resource_group" "main" {
  name     = var.resource_names.azurerm_resource_group
  location = "Australia East"
}

resource "azurerm_storage_account" "main" {
  name                     = var.resource_names.azurerm_storage_account
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  # Hardening
  min_tls_version           = "1.2"
  enable_https_traffic_only = true


}

resource "azurerm_service_plan" "main" {
  name                = var.resource_names.azurerm_service_plan
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "main" {
  name                = var.resource_names.azurerm_linux_function_app
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  storage_account_name       = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key
  service_plan_id            = azurerm_service_plan.main.id

  site_config {}
}
