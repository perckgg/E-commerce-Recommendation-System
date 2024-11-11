BEGIN TRANSACTION;
CREATE TABLE cart (
	id INTEGER NOT NULL, 
	uid INTEGER NOT NULL, 
	itemid INTEGER NOT NULL, 
	quantity INTEGER Unique NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(uid) REFERENCES users (id), 
	FOREIGN KEY(itemid) REFERENCES items (id)
);
CREATE TABLE items (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	price FLOAT NOT NULL, 
	category TEXT NOT NULL, 
	image VARCHAR(250) NOT NULL, 
	details VARCHAR(250) NOT NULL, 
	price_id VARCHAR(250) NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE comment(
	id INTEGER NOT NULL,
	content text NOT NULL,
	product_id INTEGER NOT NULL,
	user_id INTEGER NOT NULL,
	FOREIGN KEY user_id REFERENCES users(id),
	FOREIGN KEY product_id REFERENCES items(id)
);
INSERT INTO "items" VALUES(1,'iPhone 12',799.0,'Apple','https://www.gizmochina.com/wp-content/uploads/2020/05/iphone-12-pro-max-family-hero-all-600x600.jpg','6.1-inch OLED display<br>A14 Bionic chip<br>256GB storage','price_1Jk8KjBZlBPWG6ECQXNqcKhR');
INSERT INTO "items" VALUES(2,'iPhone 12 mini',729.0,'Apple','https://fdn2.gsmarena.com/vv/pics/apple/apple-iphone-12-mini-2.jpg','5.4-inch Super Retina XDR display<br>Dual 12MP camera system<br>256 GB storage','price_1Jk8LrBZlBPWG6ECvsEjYsZF');
INSERT INTO "items" VALUES(3,'iPhone 11',699.0,'Apple','https://www.gizmochina.com/wp-content/uploads/2019/09/Apple-iPhone-11-1.jpg','A13 Bionic chip<br>smart HDR<br>128GB storage','price_1Jk8MUBZlBPWG6ECueOfWc9N');
INSERT INTO "items" VALUES(4,'Acer Nitro 5',1300.0,'laptop','/static/uploads/nitro.jpg','Intel i7 10th gen<br>1920*1080 144Hz display<br>8 GB RAM<br>1 TB HDD + 256 GB SSD<br>GTX 1650 Graphics card','price_1JlBEmBZlBPWG6EC1i6RYpTB');
INSERT INTO "items" VALUES(5,'Apple MacBook Pro',1990.0,'laptop','/static/uploads/macbook.jpg','Intel core i5 2.4GHz<br>13.3" Retina Display<br>8 GB RAM<br>256 GB SSD<br>Touch Bar + Touch id','price_1JlBIQBZlBPWG6ECsPx49z0g');
INSERT INTO "items" VALUES(6,'Mi TV 4X',500.0,'Television','/static/uploads/mi%20tv.jpg','108Cm 43" UHD 4K LED<br>Smart Android TV<br>20W speakers Dolby+ DTS-HD®','price_1JlBNABZlBPWG6ECzU6Yh1dq');
CREATE TABLE ordered_items (
	id INTEGER NOT NULL, 
	oid INTEGER NOT NULL, 
	itemid INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(oid) REFERENCES orders (id), 
	FOREIGN KEY(itemid) REFERENCES items (id), 
	FOREIGN KEY(quantity) REFERENCES cart (quantity)
);
CREATE TABLE orders (
	id INTEGER NOT NULL, 
	uid INTEGER NOT NULL, 
	date timestamp NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(uid) REFERENCES users (id)
);
CREATE TABLE users (
	id INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	email VARCHAR(50) NOT NULL, 
	phone VARCHAR(50) NOT NULL, 
	password VARCHAR(250) NOT NULL, 
	admin BOOLEAN, 
	email_confirmed BOOLEAN, 
	PRIMARY KEY (id)
);
INSERT INTO "users" VALUES(1,'admin','god','1','pbkdf2:sha256:260000$kEDxo8e8$e83558e4d4e7b9e73d143929a549ec0bc595972bf9af8dd55ead9ec5c7affd65',True,True);
INSERT INTO "users" VALUES(2,'test','test','1','pbkdf2:sha256:260000$HArNj0BJ$3010254ed22cace4876325b1d51681ca1330e366c9ed819ffa3afe4d4c452f1a',False,True);
COMMIT;
ROLLBACK;