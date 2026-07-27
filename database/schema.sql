-- ======================================================
-- TELEMED AI - PRODUCTION DATABASE SCHEMA
-- Execute this entire file in Supabase SQL Editor
-- ======================================================

-- 0. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ======================================================
-- 1. ENUMS
-- ======================================================
CREATE TYPE patient_gender AS ENUM ('male', 'female', 'other');
CREATE TYPE consultation_status AS ENUM ('active', 'completed', 'cancelled');
CREATE TYPE message_sender AS ENUM ('user', 'assistant', 'system');
CREATE TYPE doctor_specialty AS ENUM (
  'general_practice', 'internal_medicine', 'pediatrics',
  'cardiology', 'neurology', 'orthopedics', 'dermatology',
  'psychiatry', 'obstetrics_gynecology', 'emergency_medicine',
  'family_medicine', 'other'
);
CREATE TYPE appointment_status AS ENUM ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show');
CREATE TYPE notification_channel AS ENUM ('email', 'sms', 'push');

-- ======================================================
-- 2. TABLES
-- ======================================================

-- 2.1 PATIENTS
CREATE TABLE IF NOT EXISTS patients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_user_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE SET NULL,
  name VARCHAR(100) NOT NULL,
  age INTEGER NOT NULL CHECK (age >= 0 AND age <= 150),
  gender patient_gender NOT NULL,
  phone VARCHAR(20),
  village VARCHAR(100),
  address TEXT,
  date_of_birth DATE,
  blood_group VARCHAR(5),
  emergency_contact_name VARCHAR(100),
  emergency_contact_phone VARCHAR(20),
  medical_history TEXT,
  allergies TEXT,
  current_medications TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.2 DOCTORS
CREATE TABLE IF NOT EXISTS doctors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_user_id UUID UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  phone VARCHAR(20),
  specialty doctor_specialty NOT NULL DEFAULT 'general_practice',
  license_number VARCHAR(50) UNIQUE,
  qualification TEXT,
  experience_years INTEGER DEFAULT 0,
  consultation_fee DECIMAL(10,2) DEFAULT 0,
  bio TEXT,
  profile_image_url TEXT,
  is_available BOOLEAN DEFAULT true,
  max_daily_consultations INTEGER DEFAULT 20,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.3 CONSULTATIONS
CREATE TABLE IF NOT EXISTS consultations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  doctor_id UUID REFERENCES doctors(id) ON DELETE SET NULL,
  status consultation_status NOT NULL DEFAULT 'active',
  chief_complaint TEXT,
  symptoms TEXT,
  severity INTEGER CHECK (severity >= 1 AND severity <= 10),
  diagnosis TEXT,
  treatment_plan TEXT,
  notes TEXT,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.4 CHAT MESSAGES
CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  consultation_id UUID NOT NULL REFERENCES consultations(id) ON DELETE CASCADE,
  sender message_sender NOT NULL,
  message TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.5 CONSULTATION SUMMARIES
CREATE TABLE IF NOT EXISTS consultation_summaries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  consultation_id UUID NOT NULL UNIQUE REFERENCES consultations(id) ON DELETE CASCADE,
  summary_text TEXT NOT NULL,
  structured_data JSONB DEFAULT '{}'::jsonb,
  status VARCHAR(20) DEFAULT 'pending',
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.6 DOCTOR NOTES
CREATE TABLE IF NOT EXISTS doctor_notes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  consultation_id UUID NOT NULL REFERENCES consultations(id) ON DELETE CASCADE,
  doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
  notes TEXT NOT NULL,
  is_private BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.7 APPOINTMENTS
CREATE TABLE IF NOT EXISTS appointments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
  consultation_id UUID REFERENCES consultations(id) ON DELETE SET NULL,
  scheduled_date TIMESTAMPTZ NOT NULL,
  status appointment_status NOT NULL DEFAULT 'scheduled',
  reason TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.8 UPLOADED FILES
CREATE TABLE IF NOT EXISTS uploaded_files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  consultation_id UUID REFERENCES consultations(id) ON DELETE SET NULL,
  file_name VARCHAR(255) NOT NULL,
  file_type VARCHAR(50) NOT NULL,
  file_size INTEGER NOT NULL,
  storage_path TEXT NOT NULL,
  signed_url TEXT,
  uploaded_by VARCHAR(50) DEFAULT 'patient',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.9 AUDIT LOGS
CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  action VARCHAR(100) NOT NULL,
  resource_type VARCHAR(50),
  resource_id UUID,
  details JSONB DEFAULT '{}'::jsonb,
  ip_address VARCHAR(45),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.10 AI PROMPT LOGS
CREATE TABLE IF NOT EXISTS ai_prompt_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  consultation_id UUID REFERENCES consultations(id) ON DELETE SET NULL,
  model_used VARCHAR(100),
  prompt_tokens INTEGER DEFAULT 0,
  completion_tokens INTEGER DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  response_time_ms INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.11 NOTIFICATIONS
CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  message TEXT NOT NULL,
  channel notification_channel DEFAULT 'email',
  is_read BOOLEAN DEFAULT false,
  metadata JSONB DEFAULT '{}'::jsonb,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ======================================================
-- 3. INDEXES
-- ======================================================

-- Patients
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name);
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);
CREATE INDEX IF NOT EXISTS idx_patients_village ON patients(village);
CREATE INDEX IF NOT EXISTS idx_patients_auth_user ON patients(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_patients_created_at ON patients(created_at DESC);

-- Doctors
CREATE INDEX IF NOT EXISTS idx_doctors_specialty ON doctors(specialty);
CREATE INDEX IF NOT EXISTS idx_doctors_availability ON doctors(is_available) WHERE is_available = true;
CREATE INDEX IF NOT EXISTS idx_doctors_auth_user ON doctors(auth_user_id);

-- Consultations
CREATE INDEX IF NOT EXISTS idx_consultations_patient ON consultations(patient_id);
CREATE INDEX IF NOT EXISTS idx_consultations_doctor ON consultations(doctor_id);
CREATE INDEX IF NOT EXISTS idx_consultations_status ON consultations(status);
CREATE INDEX IF NOT EXISTS idx_consultations_created ON consultations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_consultations_active ON consultations(patient_id) WHERE status = 'active';

-- Chat Messages
CREATE INDEX IF NOT EXISTS idx_chat_messages_consultation ON chat_messages(consultation_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(consultation_id, created_at);

-- Summaries
CREATE INDEX IF NOT EXISTS idx_summaries_consultation ON consultation_summaries(consultation_id);

-- Appointments
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);

-- Audit Logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);

-- Notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);

-- ======================================================
-- 4. TRIGGERS & FUNCTIONS
-- ======================================================

-- 4.1 Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER trigger_patients_updated_at
  BEFORE UPDATE ON patients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_doctors_updated_at
  BEFORE UPDATE ON doctors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_consultations_updated_at
  BEFORE UPDATE ON consultations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_appointments_updated_at
  BEFORE UPDATE ON appointments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_summaries_updated_at
  BEFORE UPDATE ON consultation_summaries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 4.2 Log consultation creation
CREATE OR REPLACE FUNCTION log_consultation_created()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
  VALUES (
    NEW.patient_id::uuid,
    'consultation_created',
    'consultation',
    NEW.id,
    jsonb_build_object('status', NEW.status)
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER trigger_log_consultation_created
  AFTER INSERT ON consultations FOR EACH ROW EXECUTE FUNCTION log_consultation_created();

-- 4.3 Log consultation status changes
CREATE OR REPLACE FUNCTION log_consultation_status_change()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.status <> NEW.status THEN
    INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
    VALUES (
      NEW.patient_id::uuid,
      'consultation_status_changed',
      'consultation',
      NEW.id,
      jsonb_build_object('old_status', OLD.status, 'new_status', NEW.status)
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER trigger_log_consultation_status
  AFTER UPDATE ON consultations FOR EACH ROW EXECUTE FUNCTION log_consultation_status_change();

-- 4.4 Update consultation end time
CREATE OR REPLACE FUNCTION update_consultation_end_time()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'completed' AND OLD.status = 'active' THEN
    NEW.ended_at = NOW();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_consultation_end_time
  BEFORE UPDATE ON consultations FOR EACH ROW EXECUTE FUNCTION update_consultation_end_time();

-- ======================================================
-- 5. VIEWS
-- ======================================================

-- 5.1 Patient consultation summary view
CREATE OR REPLACE VIEW patient_consultation_summary AS
SELECT
  p.id AS patient_id,
  p.name AS patient_name,
  p.age,
  p.gender,
  p.village,
  COUNT(c.id) AS total_consultations,
  COUNT(c.id) FILTER (WHERE c.status = 'active') AS active_consultations,
  COUNT(c.id) FILTER (WHERE c.status = 'completed') AS completed_consultations,
  MAX(c.created_at) AS last_consultation_date
FROM patients p
LEFT JOIN consultations c ON c.patient_id = p.id
GROUP BY p.id, p.name, p.age, p.gender, p.village;

-- 5.2 Doctor workload view
CREATE OR REPLACE VIEW doctor_workload AS
SELECT
  d.id AS doctor_id,
  d.name AS doctor_name,
  d.specialty,
  COUNT(c.id) AS total_consultations,
  COUNT(c.id) FILTER (WHERE c.status = 'active') AS active_consultations,
  COUNT(c.id) FILTER (WHERE c.created_at >= NOW() - INTERVAL '7 days') AS weekly_consultations,
  COUNT(DISTINCT c.patient_id) AS unique_patients
FROM doctors d
LEFT JOIN consultations c ON c.doctor_id = d.id
GROUP BY d.id, d.name, d.specialty;

-- 5.3 Daily consultation stats
CREATE OR REPLACE VIEW daily_consultation_stats AS
SELECT
  DATE(created_at) AS consultation_date,
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE status = 'active') AS active,
  COUNT(*) FILTER (WHERE status = 'completed') AS completed,
  COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled
FROM consultations
GROUP BY DATE(created_at)
ORDER BY consultation_date DESC;

-- ======================================================
-- 6. ROW LEVEL SECURITY POLICIES
-- ======================================================

-- Enable RLS on all tables
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctors ENABLE ROW LEVEL SECURITY;
ALTER TABLE consultations ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE consultation_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctor_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE uploaded_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_prompt_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- 6.1 Patients policies
CREATE POLICY "Patients can view own record"
  ON patients FOR SELECT
  USING (auth_user_id = auth.uid());

CREATE POLICY "Service role can manage patients"
  ON patients FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "Doctors can view patients"
  ON patients FOR SELECT
  USING (
    EXISTS (SELECT 1 FROM doctors WHERE auth_user_id = auth.uid())
  );

-- 6.2 Doctors policies
CREATE POLICY "Doctors can view own profile"
  ON doctors FOR SELECT
  USING (auth_user_id = auth.uid());

CREATE POLICY "Service role can manage doctors"
  ON doctors FOR ALL
  USING (auth.role() = 'service_role');

-- 6.3 Consultations policies
CREATE POLICY "Patients can view own consultations"
  ON consultations FOR SELECT
  USING (
    patient_id IN (SELECT id FROM patients WHERE auth_user_id = auth.uid())
  );

CREATE POLICY "Doctors can view assigned consultations"
  ON consultations FOR SELECT
  USING (
    doctor_id IN (SELECT id FROM doctors WHERE auth_user_id = auth.uid())
  );

CREATE POLICY "Service role can manage consultations"
  ON consultations FOR ALL
  USING (auth.role() = 'service_role');

-- 6.4 Chat messages policies
CREATE POLICY "Users can view messages in their consultations"
  ON chat_messages FOR SELECT
  USING (
    consultation_id IN (
      SELECT id FROM consultations WHERE
        patient_id IN (SELECT id FROM patients WHERE auth_user_id = auth.uid())
        OR
        doctor_id IN (SELECT id FROM doctors WHERE auth_user_id = auth.uid())
    )
  );

-- 6.5 Notifications policies
CREATE POLICY "Users can view own notifications"
  ON notifications FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can update own notifications"
  ON notifications FOR UPDATE
  USING (user_id = auth.uid());

-- ======================================================
-- 7. STORAGE SETUP (Run separately in Supabase Dashboard)
-- ======================================================
-- MANUAL STEPS:
-- 1. Go to Supabase Dashboard → Storage → Create bucket
-- 2. Bucket name: medical-files
-- 3. Make it private
-- 4. Add policy: Allow authenticated users to read/write their own files
-- 5. Add policy: Allow doctors to read patient files

-- ======================================================
-- 8. SEED DATA (Optional - for testing)
-- ======================================================

-- INSERT INTO patients (name, age, gender, phone, village)
-- VALUES
--   ('John Doe', 35, 'male', '9876543210', 'Springfield'),
--   ('Jane Smith', 28, 'female', '9876543211', 'Shelbyville');

-- INSERT INTO consultations (patient_id, status)
-- VALUES
--   ((SELECT id FROM patients LIMIT 1), 'active');

