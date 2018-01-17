resource "aws_security_group" "allow_ssh" {
  name        = "allow_all"
  description = "Allow inbound SSH traffic from my everywhere"
  vpc_id      = "vpc-ced904a9"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags {
    Name = "Allow SSH"
  }
}

variable "aws_region" {
  default = "eu-west-1"
}

variable "aws_key_name" {
  default = "franzi"
}

variable "aws_profile" {
  default = "franzi"
}
