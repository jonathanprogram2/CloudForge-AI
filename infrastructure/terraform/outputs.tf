
output "aws_region" {
  value = var.aws_region
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "load_balancer_url" {
  value = "https://${aws_lb.api.dns_name}"
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.api.name
}
