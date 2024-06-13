# Container Server

This Rust program facilitates the downloading and setting up Docker Compose files. It allows users to manage and list applications and authors, and to copy relevant Docker Compose files to specified directories.

## Features

- **Download and Extract Docker Compose Files**: Automatically download and extract the latest Docker Compose files from <https://github.com/luigi311/Container-Server-Templates>
- **List Apps and Authors**: List all available apps and authors in the data.
- **Match App and Author Names**: Find the closest matches for app and author names using the Jaro-Winkler similarity metric.
- **Copy Docker Compose Files**: Copy Docker Compose files to a specified output directory.

## Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/luigi311/Container-Server.git
   cd Container-Server
   ```

2. **Build the project**:
   ```sh
   cargo build --release
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root and add the following variables:
   ```sh
   TEMPLATES_FOLDER=Docker_Compose
   DOCKER_COMPOSE_FOLDER=.
   ```

## Usage

```sh
container-server [OPTIONS]
```

### Options

- `--app <APP>`: Specify the app name.
- `--author <AUTHOR>`: Specify the author name.
- `--list-apps`: List all the apps.
- `--list-authors`: List all the authors.
- `--update`: Update the Docker Compose folder by downloading and extracting the latest files.

### Examples

- **List all apps**:
  ```sh
  container-server --list-apps
  ```

- **List all authors**:
  ```sh
  container-server --list-authors
  ```

- **Find a specific app and list its authors**:
  ```sh
  container-server --app <APP_NAME>
  ```

- **Find a specific author and list their apps**:
  ```sh
  container-server --author <AUTHOR_NAME>
  ```

- **Copy Docker Compose file for a specific app and author**:
  ```sh
  container-server --app <APP_NAME> --author <AUTHOR_NAME>
  ```

- **Update the Docker Compose folder**:
  ```sh
  container-server --update
  ```

## Environment Variables

- `TEMPLATES_FOLDER`: The folder containing the Docker Compose templates.
- `DOCKER_COMPOSE_FOLDER`: The output directory where Docker Compose files will be copied.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

## License

This project is licensed under the GNUv3 License. See the `LICENSE` file for more information.
