1. create ubuntu 2 GB ram, 20 gb hard ec2


2. Install MySQL Server on your Ubuntu instance:
sudo apt update
sudo apt install mysql-server

3. Log in to MySQL:
sudo su
mysql -u root -p
give a password  (12345)

4. Create a database and user, and grant privileges:
CREATE DATABASE broodbox;
CREATE USER 'dilshan'@'localhost' IDENTIFIED BY '1234'; 
GRANT ALL PRIVILEGES ON broodbox.* TO 'dilshan'@'localhost';
FLUSH PRIVILEGES;
(here 1234 the password of the user)

5.create table
USE broodbox;
CREATE TABLE `farm_details` (
 `business_id` VARCHAR(255), `farm_id` VARCHAR(255) PRIMARY KEY, `boundaries` TEXT);

6.insert values
INSERT INTO `farm_details` (`business_id`, `farm_id`, `boundaries`)
VALUES
('B456', '123', '[(123,344),(434.3,34.5),(434.3,34.5),(434.3,34.5)(434.3,34.5)(434.3,34.5)(434.3,34.5)(434.3,34.5)(434.3,34.5),(434.3,34.5)]'),
('B678', '456', 'Boundary 2'),
('B999', '78t', 'Boundary 3');

7.create table
CREATE TABLE `hive_details_B456_123` (
 `area_code` VARCHAR(255), `location_code` VARCHAR(255),  `longitude` double, 
`latitude` double, `total_beehives` int(200), `total_active_frames` int(200),
`img_urls` TEXT,
PRIMARY KEY (`area_code`, `location_code`));

8. clone the git repo
open new terminal 
git clone https://github.com/Chamika-ML/database-api4.git


9. insert hvie_details.csv file data to table

go to first
a) SHOW VARIABLES LIKE "secure_file_priv";
   copy  the valu path ( /var/lib/mysql-files/ )

go to second terminal
b) sudo mv /home/ubuntu/database-api4/hive_details.csv /var/lib/mysql-files/

go to first terminal
c) LOAD DATA INFILE '/var/lib/mysql-files/hive_details.csv'
   INTO TABLE `hive_details_B456_123`
   FIELDS TERMINATED BY ','
   OPTIONALLY ENCLOSED BY '"'
   LINES TERMINATED BY '\n'
   IGNORE 1 LINES;

d)SELECT * FROM `hive_details_B456_123`; 

10. change the line main.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://dilshan:1234@localhost/broodbox'


11. make virtual env for run api

go to second terminal
cd database-api4
sudo apt-get install python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

if tere are (MYSQLdb install errors, then run below):
sudo apt-get install -y libmysqlclient-dev pkg-config
sudo apt-get install build-essential
sudo apt-get install python3-dev



12.Run 
gunicorn -w 4 -b 0.0.0.0:5000 main:app

13. test the api:

insall thunder client to the vs code

GET

* http://ec2-54-206-119-102.ap-southeast-2.compute.amazonaws.com:5000/farm

* http://ec2-54-206-119-102.ap-southeast-2.compute.amazonaws.com:5000/farm/123

* http://ec2-54-206-119-102.ap-southeast-2.compute.amazonaws.com:5000/hive/B456/123

* http://ec2-54-206-119-102.ap-southeast-2.compute.amazonaws.com:5000/hive/area-location-codes/B456/123

* http://ec2-54-206-119-102.ap-southeast-2.compute.amazonaws.com:5000/hive/get/B456/123/1/11139 


POST

* http://ec2-54-206-119-102.ap-southeast-2.compute.amazonaws.com:5000/farm/add
{ 
  "business_id":"asd12",
  "farm_id":343,
  "boundaries":"boundry 12445"
}

* http://ec2-54-206-119-102.ap-southeast-2.compute.amazonaws.com:5000/farm/delete/343

* http://ec2-54-206-119-102.ap-southeast-2.compute.amazonaws.com:5000/farm/edit/456

{
  "farm_id":456,
  "boundaries":"This is the new boundary for id 456"
}

* http://ec2-54-206-119-102.ap-southeast-2.compute.amazonaws.com:5000/hive/add/B456/123 

{"data": [{
  "area_code":987654,
  "location_code":12345,
  "longitude":12.3456,
  "latitude":-123.4567,
  "total_beehives":1000
},
{"area_code":321456,
  "location_code":67534,
  "longitude":22.3456,
  "latitude":-563.4567,
  "total_beehives":400
}
]}

* http://ec2-54-206-119-102.ap-southeast-2.compute.amazonaws.com:5000/hive/update/B456/123/987654/12345

{
  "area_code":"This is the new",
  "location_code":54321,
  "longitude":1212.3456,
  "latitude":6123.4567,
  "total_beehives":15000,
  "img_urls": "[abc,bbc,ccc]"   
}

* http://ec2-54-206-119-102.ap-southeast-2.compute.amazonaws.com:5000/hive/delete/B456/123/321456/67534
* http://ec2-54-206-119-102.ap-southeast-2.compute.amazonaws.com:5000/hive/delete/B456/123/This is the new/54321


actual_boundaries = [(-35.11385326200778, 143.25293763434638),(-35.114063892991425, 143.28194840705146),(-35.1427046337376, 143.28126176154365),(-35.142564262517844, 143.30881341254462),(-35.11383815350994, 143.30926501961525),(-35.113487100595464, 143.315702321251),(-35.084906321686866, 143.3134707233506),(-35.085117027471874, 143.25570667000588)]



