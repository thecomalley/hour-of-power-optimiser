data "azurerm_client_config" "current" {}

module "terraform_azurerm_python_function" {
  source  = "thecomalley/python-function/azurerm"
  version = "1.2.0"

  location = "Australia East"

  # { organization }-{ workload }-{ environment }-{ region }-{ component }-{ ResourceType }
  resource_group_name       = "oma-hop-hprd-aue-rg"
  function_app_name         = "oma-hop-hprd-aue-func"
  storage_account_name      = "omahophprdauest"
  log_analytics_name        = "oma-hop-hprd-aue-law"
  app_service_plan_name     = "oma-hop-hprd-aue-asp"
  application_insights_name = "oma-hop-hprd-aue-ai"
  key_vault_name            = "oma-hop-hprd-aue-kv"

  python_version = "3.11"

  # must be a relative path to ${path.module}
  python_source_code_path = "../src"

  secret_environment_variables = [
    "ELECTRIC_KIWI_EMAIL",
    "ELECTRIC_KIWI_PASSWORD",
    "HOME_ASSISTANT_ACCESS_TOKEN",
    "HOME_ASSISTANT_ENTITY_ID",
    "HOME_ASSISTANT_URL",
    "PUSHOVER_API_TOKEN",
    "PUSHOVER_USER_KEY"
  ]

  tags = {
    WorkloadName = "Hour of Power Optimiser"
    Environment  = "Home Production"
  }
}
