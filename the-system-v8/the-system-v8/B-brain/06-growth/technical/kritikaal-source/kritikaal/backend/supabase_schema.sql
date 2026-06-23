CREATE TABLE clients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT,
  company TEXT,
  country TEXT,
  leather_design TEXT,
  stage TEXT DEFAULT 'Lead & Call Booking',
  source TEXT DEFAULT 'Website',
  created_at TIMESTAMP DEFAULT NOW(),
  deleted BOOLEAN DEFAULT false,
  deleted_reason TEXT
);

CREATE TABLE notes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  client_id uuid REFERENCES clients(id) ON DELETE CASCADE
);

CREATE TABLE notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT,
  content TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  client_id uuid REFERENCES clients(id) ON DELETE CASCADE
);