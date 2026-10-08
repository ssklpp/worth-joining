-- docker-compose.yml 전용. worth_joining과 wj 계정은 이미지 환경 변수로 만들어진다.
CREATE DATABASE IF NOT EXISTS worth_joining_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON worth_joining_test.* TO 'wj'@'%';
