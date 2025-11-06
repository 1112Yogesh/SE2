docker build -t project-analyzer .
docker run --rm -v "$(pwd):/projects" project-analyzer