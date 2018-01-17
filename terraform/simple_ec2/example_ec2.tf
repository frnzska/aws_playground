provider "aws" {
  region  = "eu-west-1"
  profile = "franzi"
}

resource "aws_instance" "example" {
  ami             = "ami-e5083683"
  instance_type   = "t2.micro"
  key_name        = "franzi"
  security_groups = ["${aws_security_group.allow_ssh.name}"]

  tags {
    Name = "my_instance_name"
  }
}

resource "aws_security_group" "allow_ssh" {
  name        = "allow_ssh"
  description = "Allow inbound SSH traffic from everywhere"
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
