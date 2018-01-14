provider "aws" {
  region  = "eu-west-1"
  profile = "franzi"
}

resource "aws_instance" "example" {
  ami           = "ami-e5083683"
  instance_type = "t2.micro"

  tags {
    Name = "my_instance_name"
  }
}
