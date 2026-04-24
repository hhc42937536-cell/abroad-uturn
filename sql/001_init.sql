CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  line_user_id VARCHAR(50) UNIQUE NOT NULL,
  display_name VARCHAR(100),
  departure_city VARCHAR(50) DEFAULT 'Taipei',
  departure_airport CHAR(3) DEFAULT 'TPE',
  preferred_currency CHAR(3) DEFAULT 'TWD',
  language VARCHAR(10) DEFAULT 'zh-TW',
  default_traveler_count INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  line_user_id VARCHAR(50) NOT NULL,
  module VARCHAR(20) NOT NULL,
  step INT DEFAULT 0,
  state JSONB DEFAULT '{}',
  expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '2 hours',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(line_user_id),
  FOREIGN KEY (line_user_id) REFERENCES users(line_user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS itineraries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  line_user_id VARCHAR(50) NOT NULL,
  module VARCHAR(20),
  destination VARCHAR(100),
  start_date DATE,
  end_date DATE,
  traveler_count INT DEFAULT 1,
  budget_twd INT,
  content JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (line_user_id) REFERENCES users(line_user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS star_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  line_user_id VARCHAR(50) NOT NULL,
  artist_name VARCHAR(100),
  event_type VARCHAR(50),
  event_date DATE,
  venue_city VARCHAR(100),
  itinerary_id UUID REFERENCES itineraries(id) ON DELETE SET NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (line_user_id) REFERENCES users(line_user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS api_cache (
  cache_key VARCHAR(255) PRIMARY KEY,
  data JSONB,
  expires_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS price_tracks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  line_user_id VARCHAR(50) NOT NULL,
  origin_airport CHAR(3) NOT NULL,
  destination_airport CHAR(3) NOT NULL,
  depart_date DATE,
  return_date DATE,
  last_price_twd INT,
  enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (line_user_id) REFERENCES users(line_user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_itineraries_line_user_id ON itineraries(line_user_id);
CREATE INDEX IF NOT EXISTS idx_api_cache_expires_at ON api_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_price_tracks_enabled ON price_tracks(enabled);
