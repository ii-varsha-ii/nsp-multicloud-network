# output "cidr_block" {
#   description = "cidr block of VPC 1"
#   value = var.vpc_1_cidr_block
# }

# output "vpc_1_id" {
#   description = "VPC details"
#   value = {
#     "id" = aws_vpc.aws_vpc_1.id
#     "cidr" = aws_vpc.aws_vpc_1.cidr_block
#     "name" = aws_vpc.aws_vpc_1.tags.Name
#   }
# }