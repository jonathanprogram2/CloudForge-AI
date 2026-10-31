
variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-2"
}

variable "project_name" {
  description = "Resource naming prefix"
  type        = string
  default     = "cloudforge-ai"
}

variable "container_image" {
  description = "ECR container image URI"
  type        = string
  default     = "public.ecr.aws/docker/library/python:3.10-slim"
}

variable "container_port" {
  description = "FastAPI listening port"
  type        = number
  default     = 8000
}

variable "task_count" {
  description = "Number of running ECS tasks"
  type        = number
  default     = 1

  validation {
    condition     = var.task_count >= 0 && var.task_count <= 2
    error_message = "Task count must be between 0 and 2."
  }
}
