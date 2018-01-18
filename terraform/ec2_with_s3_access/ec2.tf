provider "aws" {
  region  = "${var.aws_region}"
  profile = "${var.aws_profile}"
}

### IAM ###

data aws_iam_policy_document "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

data aws_iam_policy_document "s3_read_access" {
  statement {
    actions = ["s3:Get*", "s3:List*"]

    resources = ["arn:aws:s3:::*"]
  }
}

resource "aws_iam_role" "ec2_iam_role" {
  name = "ec2_iam_role"

  assume_role_policy = "${data.aws_iam_policy_document.ec2_assume_role.json}"
}

resource "aws_iam_role_policy" "join_policy" {
  depends_on = ["aws_iam_role.ec2_iam_role"]
  name       = "join_policy"
  role       = "${aws_iam_role.ec2_iam_role.name}"

  policy = "${data.aws_iam_policy_document.s3_read_access.json}"
}

resource "aws_iam_instance_profile" "instance_profile" {
  name = "instance_profile"
  role = "${aws_iam_role.ec2_iam_role.name}"
}

### Instance ###

resource "aws_instance" "example" {
  ami                  = "ami-e5083683"
  instance_type        = "t2.micro"
  key_name             = "${var.aws_key_name}"
  security_groups      = ["${aws_security_group.ssh.name}"]
  iam_instance_profile = "${aws_iam_instance_profile.instance_profile.name}"

  tags {
    Name = "instance_with_s3_access"
  }
}

resource "aws_security_group" "ssh" {
  name        = "ssh"
  description = "Allow SSH traffic from everywhere"
  vpc_id      = "vpc-ced904a9"
}

resource "aws_security_group_rule" "ssh_ingress" {
  security_group_id = "${aws_security_group.ssh.id}"
  type              = "ingress"
  protocol          = "tcp"
  from_port         = 22
  to_port           = 22
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "ssh_egress" {
  security_group_id = "${aws_security_group.ssh.id}"
  type              = "egress"
  protocol          = "-1"
  from_port         = 0
  to_port           = 0
  cidr_blocks       = ["0.0.0.0/0"]
}
