# In this module we create the container resources - AWS ECR, AWS ECS Cluster, AWS ECS Task Definition, AWS ECS Service

# resource "aws_ecr_repository" "this" {
#   for_each = toset(var.repository_names)

#   name = each.value

#   image_scanning_configuration {
#     scan_on_push = true
#   }

#   image_tag_mutability = "MUTABLE"

#   tags = merge(var.tags, {
#     Name = each.value
#   })
# }
data "aws_caller_identity" "current" {}

resource "aws_ecs_cluster" "this" {
  name = var.cluster_name

  tags = merge(var.tags, {
    Name = var.cluster_name
  })
}

resource "aws_ecs_task_definition" "this" {
  for_each = toset(var.service_names)

  family                   = each.value
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/ecs-task-execution-role"
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = each.value
      # image     = "${aws_ecr_repository.this[each.value].repository_url}:latest"
      image     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-east-2.amazonaws.com/${each.value}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = lookup(var.task_environment, each.value, [])
      secrets     = lookup(var.secrets, each.value, [])
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${each.value}"
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = each.value
          "awslogs-create-group"  = "true"
        }
      }
    }
  ])

  tags = merge(var.tags, {
    Name = each.value
  })
}

resource "aws_ecs_service" "this" {
  for_each = toset(var.service_names)

  name            = each.value
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.this[each.value].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = var.security_group_ids
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this[each.key].arn
    container_name   = each.value
    container_port   = 8000
  }

  # Enable ECS Service Auto Scaling
  deployment_controller {
    type = "ECS"
  }

  tags = merge(var.tags, {
    Name = each.value
  })
}

resource "aws_appautoscaling_target" "this" {
  for_each = toset(var.service_names)

  max_capacity       = 5
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.this.name}/${aws_ecs_service.this[each.value].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu_scaling" {
  for_each = toset(var.service_names)

  name               = "${each.value}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.this[each.value].resource_id
  scalable_dimension = aws_appautoscaling_target.this[each.value].scalable_dimension
  service_namespace  = aws_appautoscaling_target.this[each.value].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }

    target_value       = 80.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}

resource "aws_lb_target_group" "this" {
  for_each = toset(var.service_names)

  name        = "${each.value}-tg"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    path                = "/${each.value}/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200"
  }

  tags = merge(var.tags, {
    Name = "${each.value}-tg"
  })
}

resource "aws_lb_listener_rule" "this" {
  for_each = toset(var.service_names)

  listener_arn = var.alb_listener_arn
  priority     = 100 + index(var.service_names, each.key)

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this[each.key].arn
  }

  condition {
    path_pattern {
      values = [var.service_paths[each.key], "${var.service_paths[each.key]}*", "${var.service_paths[each.key]}/*"]
    }
  }
}