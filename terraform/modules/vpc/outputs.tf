# Outputs
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = [for subnet in aws_subnet.public : subnet.id]
}

output "private_subnet_ids" {
  value = [for subnet in aws_subnet.private : subnet.id]
}

output "alb_security_group_id" {
  value = aws_security_group.alb_sg.id
}

output "internal_security_group_id" {
  value = aws_security_group.svc_to_svc_sg.id
}

output "database_security_group_id" {
  value = aws_security_group.rds_postgres_sg.id
}

output "database_subnet_group_name" {
  value = aws_db_subnet_group.rds.name
  
}

output "load_balancer_arn" {
  value = aws_lb.main.arn
  
}

output "alb_listener_arn" {
  value = aws_alb_listener.http.arn
}