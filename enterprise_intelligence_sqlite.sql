PRAGMA foreign_keys = ON;

-- Customers
DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
  customer_id TEXT PRIMARY KEY,
  name TEXT,
  email TEXT,
  location TEXT
);

-- Delivery agents
DROP TABLE IF EXISTS delivery_agents;
CREATE TABLE delivery_agents (
  agent_id TEXT PRIMARY KEY,
  name TEXT,
  vehicle_type TEXT,
  base_location TEXT
);

-- Orders
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
  order_id TEXT PRIMARY KEY,
  customer_id TEXT,
  agent_id TEXT,
  order_status TEXT,
  order_time TEXT,     -- stored as ISO-8601 string "YYYY-MM-DD HH:MM:SS"
  delivery_time TEXT,  -- NULL allowed
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  FOREIGN KEY (agent_id) REFERENCES delivery_agents(agent_id)
);

-- Customer reviews
DROP TABLE IF EXISTS customer_reviews;
CREATE TABLE customer_reviews (
  review_id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id TEXT,
  review_text TEXT,
  sentiment TEXT,
  FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Incidents
DROP TABLE IF EXISTS incidents;
CREATE TABLE incidents (
  incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id TEXT,
  order_id TEXT,
  issue_type TEXT,
  reported_at TEXT,
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Helpful indexes (optional but good)
CREATE INDEX IF NOT EXISTS idx_customer_reviews_order_id ON customer_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_incidents_customer_id ON incidents(customer_id);
CREATE INDEX IF NOT EXISTS idx_incidents_order_id ON incidents(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_agent_id ON orders(agent_id);

-- Data
INSERT INTO customers (customer_id, name, email, location) VALUES
('101', 'Arun Kumar', 'arun.kumar@gmail.com', 'Kochi'),
('104', 'Ravi Menon', 'ravi.menon@gmail.com', 'Trivandrum'),
('107', 'Anjali Nair', 'anjali.nair@gmail.com', 'Ernakulam'),
('109', 'Priya Sharma', 'priya.sharma@gmail.com', 'Bangalore'),
('113', 'Suresh Das', 'suresh.das@gmail.com', 'Chennai'),
('118', 'Neha Gupta', 'neha.gupta@gmail.com', 'Delhi'),
('121', 'Vijay Rao', 'vijay.rao@gmail.com', 'Hyderabad'),
('124', 'Amit Singh', 'amit.singh@gmail.com', 'Pune'),
('129', 'Karthik Iyer', 'karthik.iyer@gmail.com', 'Coimbatore'),
('132', 'Meera Pillai', 'meera.pillai@gmail.com', 'Kollam');

INSERT INTO delivery_agents (agent_id, name, vehicle_type, base_location) VALUES
('201', 'Rahul Das', 'Bike', 'Kochi'),
('204', 'Amit Singh', 'Scooter', 'Bangalore'),
('207', 'Suresh Kumar', 'Bike', 'Chennai'),
('210', 'Vijay Nair', 'Van', 'Trivandrum'),
('214', 'Manoj Rao', 'Bike', 'Hyderabad'),
('217', 'Kiran Rao', 'Bike', 'Mumbai'),
('220', 'Sanjay Patel', 'Scooter', 'Ahmedabad'),
('223', 'Imran Khan', 'Bike', 'Delhi'),
('226', 'Rohit Malhotra', 'Car', 'Gurgaon'),
('229', 'Arjun Pillai', 'Bike', 'Kollam');

INSERT INTO orders (order_id, customer_id, agent_id, order_status, order_time, delivery_time) VALUES
('501', '101', '201', 'Delivered', '2026-01-10 13:00:00', '2026-01-10 13:30:00'),
('504', '104', '204', 'Delivered', '2026-01-10 14:00:00', '2026-01-10 14:45:00'),
('507', '107', '207', 'Delayed', '2026-01-10 18:30:00', NULL),
('509', '109', '210', 'Cancelled', '2026-01-09 19:00:00', NULL),
('513', '113', '214', 'Delivered', '2026-01-11 12:15:00', '2026-01-11 12:55:00'),
('516', '101', '217', 'Delivered', '2026-01-12 13:10:00', '2026-01-12 13:40:00'),
('519', '104', '220', 'Delivered', '2026-01-12 14:00:00', '2026-01-12 14:35:00'),
('522', '107', '223', 'Delayed', '2026-01-12 18:20:00', NULL),
('525', '109', '226', 'Cancelled', '2026-01-13 19:10:00', NULL),
('528', '113', '229', 'Delivered', '2026-01-13 12:00:00', '2026-01-13 12:30:00');

INSERT INTO customer_reviews (review_id, order_id, review_text, sentiment) VALUES
(1, '501', 'Delivery was fast and smooth', 'Positive'),
(2, '504', 'Agent was polite but delivery was slow', 'Neutral'),
(3, '507', 'Very late delivery, no updates', 'Negative'),
(4, '509', 'Order cancelled without notice', 'Negative'),
(5, '513', 'Food arrived hot and on time', 'Positive'),
(6, '516', 'Quick delivery and friendly agent', 'Positive'),
(7, '519', 'Slight delay but acceptable', 'Neutral'),
(8, '522', 'Delivery was very late', 'Negative'),
(9, '525', 'Order cancelled unexpectedly', 'Negative'),
(10, '528', 'Food arrived hot and fresh', 'Positive');

-- If you omit incident_id here, SQLite will autogenerate it.
INSERT INTO incidents (incident_id, customer_id, order_id, issue_type, reported_at) VALUES
(1, '107', '507', 'Delivery Delay', '2026-01-10 20:00:00'),
(2, '109', '509', 'Cancellation Not Reflected', '2026-01-09 21:00:00'),
(3, '113', '513', 'Late Delivery', '2026-01-11 13:30:00'),
(4, '101', '516', 'Minor Delay', '2026-01-12 14:00:00'),
(5, '104', '519', 'Late Delivery', '2026-01-12 15:00:00'),
(6, '107', '522', 'Delivery Delay', '2026-01-12 21:00:00'),
(7, '109', '525', 'Cancellation Issue', '2026-01-13 20:00:00'),
(8, '113', '528', 'Late Delivery', '2026-01-13 13:30:00'),
(9, '118', '504', 'Agent Behaviour', '2026-01-10 15:10:00'),
(10, '121', '501', 'Wrong Address', '2026-01-10 13:40:00');
