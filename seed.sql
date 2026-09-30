INSERT OR IGNORE INTO categories(id,name,sort_order) VALUES
(1,'Pa artesanal',1),(2,'Brioixeria i dolços',2),(3,'Especialitats',3),(4,'Cafeteria',4),(5,'Entrepans i creps',5);
INSERT OR IGNORE INTO products(id,category_id,name,description,price,featured,sort_order) VALUES
(1,1,'Pa de pagès','Pa tradicional de la casa.',3.20,1,1),
(2,1,'Pa d’espelta','Pa artesanal d’espelta.',3.80,0,2),
(3,1,'Pa de cereals','Pa amb barreja de cereals.',3.80,0,3),
(4,2,'Croissant','Brioixeria de mantega.',1.60,1,1),
(5,2,'Croissant de crema','Croissant farcit de crema.',2.30,1,2),
(6,2,'Donut gegant','Especialitat coneguda de Forn Baltà.',3.50,1,3),
(7,2,'Xuxo','Brioixeria tradicional farcida.',2.50,0,4),
(8,3,'Coca de crema','Especialitat de pastisseria.',3.50,1,1),
(9,3,'Panellets','Producte estacional; confirmar disponibilitat.',4.90,0,2),
(10,4,'Cafè amb llet','Cafè amb llet.',2.10,1,1),
(11,4,'Cortado','Cafè curt amb una mica de llet.',1.80,0,2),
(12,5,'Entrepà de la casa','Entrepà preparat al moment.',4.90,0,1),
(13,5,'Crep amb xocolata','Crep dolça amb xocolata.',4.50,1,2);
