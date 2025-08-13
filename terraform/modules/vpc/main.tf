# We are creating a VPC with a public subnet and an internet gateway.
# Let's also create a security group that allows inbound traffic on port 80 and 443.
# We shall also think about VPC Endpoints where applicable.
resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
  enable_dns_support = true
  enable_dns_hostnames = true
  tags = merge(
    { Name = "main-vpc" },
    var.tags
  )
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
  tags = merge(
    var.tags,
    { Name = "main-igw" }
  )
}

resource "aws_eip" "nat" {
  # vpc = true
  tags = merge(
  var.tags,
  {
    Name = "main-nat-eip"
  }
  )
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  tags = merge(
  var.tags, 
  { Name = "main-nat-gw" }
  )
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnets)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnets[count.index]
  map_public_ip_on_launch = true
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  tags = merge(
    var.tags, 
    { Name = "public-subnet-${count.index + 1}" } 
  )
}

resource "aws_subnet" "private" {
  count             = length(var.private_subnets)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnets[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = merge(
    var.tags, 
    { Name = "private-subnet-${count.index + 1}" } 
  )
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
  tags = merge(var.tags, { Name = "public-rt" })
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }
  tags = merge(var.tags, { Name = "private-rt" })
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_security_group" "alb_sg" {
  name        = "alb-sg"
  description = "Allow HTTP and HTTPS"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "alb-sg" })
}

resource "aws_security_group" "svc_to_svc_sg" {
  name        = "svc-to-svc"
  description = "Allow internal service-to-service communication on 8000-8010"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 8000
    to_port     = 8010
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "svc-to-svc-sg" }) 
}

resource "aws_security_group" "rds_postgres_sg" {
  name        = "rds-postgres-sg"
  description = "Allow Postgres access from svc-to-svc-sg"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.svc_to_svc_sg.id]
  }

  ingress  {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    security_groups = [aws_security_group.svc_to_svc_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "rds-postgres-sg" })
}

resource "aws_security_group_rule" "svc_to_svc_from_rds" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.svc_to_svc_sg.id
  source_security_group_id = aws_security_group.rds_postgres_sg.id
  description              = "Allow Postgres traffic from RDS SG"
}

resource "aws_security_group_rule" "svc_to_svc_from_redis" {
  type                     = "ingress"
  from_port                = 6379
  to_port                  = 6379
  protocol                 = "tcp"
  security_group_id        = aws_security_group.svc_to_svc_sg.id
  source_security_group_id = aws_security_group.rds_postgres_sg.id
  description              = "Allow Redis traffic from RDS SG"
}

resource "aws_db_subnet_group" "rds" {
  name       = "datastore-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  tags = merge(
    var.tags,
    { Name = "datastore-subnet-group" }
  )
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "redis-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  description = "Subnet group for Redis cluster"
  tags = merge(
    var.tags,
    { Name = "redis-subnet-group" }
  )
}

resource "aws_lb" "main" {
  name               = "main-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = aws_subnet.private[*].id

  tags = merge(
    var.tags,
    { Name = "main-alb" }
  )
}

resource "aws_alb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "ALB is healthy"
      status_code  = "200"
    }
  }

  tags = merge(
    var.tags,
    { Name = "main-alb-http-listener" }
  )
  
}

# VPC Link for API Gateway to connect to ALB
resource "aws_apigatewayv2_vpc_link" "vpc_link" {
  name        = "main-vpc-link"
  security_group_ids = [aws_security_group.alb_sg.id]
  subnet_ids  = aws_subnet.private[*].id

  tags = merge(
    var.tags,
    { Name = "main-vpc-link" }
  )
}

data "aws_availability_zones" "available" {}