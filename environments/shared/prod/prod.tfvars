subscription_id     = "4829f1ca-01f5-4dbc-9056-c67a84c89515"
prefix              = "prod"
resource_group_name = "rg-fonteyn-prod"
address_space       = ["10.20.0.0/16"]
tags = {
  Environment = "Development"
  Owner       = "t.duicu@student.fontys.nl"
  Project     = "Fonteyn Cloud Infrastructure"
}
subnets = [
    {
      name           = "app"
      address_prefix = "10.20.1.0/24"
    },
    {
      name           = "db"
      address_prefix = "10.20.2.0/24"
    },
    {
      name           = "sensor"
      address_prefix = "10.20.3.0/24"
    }
]