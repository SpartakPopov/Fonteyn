subscription_id     = "4829f1ca-01f5-4dbc-9056-c67a84c89515"
prefix              = "dev"
resource_group_name = "rg-fonteyn-dev"
address_space       = ["10.10.0.0/16"]
tags = {
  Environment = "Production"
  Owner       = "t.duicu@student.fontys.nl"
  Project     = "Fonteyn Cloud Infrastructure"
}
subnets = [
    {
      name           = "app"
      address_prefix = "10.10.1.0/24"
    },
    {
      name           = "db"
      address_prefix = "10.10.2.0/24"
    },
    {
      name           = "sensor"
      address_prefix = "10.10.3.0/24"
    }
]