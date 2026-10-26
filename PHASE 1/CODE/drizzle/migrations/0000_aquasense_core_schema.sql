-- Enums
CREATE TYPE public.app_role AS ENUM ('admin', 'engineer', 'viewer');
CREATE TYPE public.device_status AS ENUM ('online', 'offline', 'maintenance');
CREATE TYPE public.leak_severity AS ENUM ('critical', 'high', 'medium', 'low');
CREATE TYPE public.leak_status AS ENUM ('active', 'investigating', 'resolved');
CREATE TYPE public.notification_severity AS ENUM ('critical', 'high', 'medium', 'low', 'info');

-- Profiles
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT NOT NULL DEFAULT '',
  email TEXT NOT NULL DEFAULT '',
  zone TEXT NOT NULL DEFAULT 'All zones',
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.profiles TO authenticated;
GRANT ALL ON public.profiles TO service_role;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Roles
CREATE TABLE public.user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role public.app_role NOT NULL,
  UNIQUE (user_id, role)
);
GRANT SELECT ON public.user_roles TO authenticated;
GRANT ALL ON public.user_roles TO service_role;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.has_role(_user_id UUID, _role public.app_role)
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT EXISTS (SELECT 1 FROM public.user_roles WHERE user_id = _user_id AND role = _role)
$$;

CREATE POLICY "Users read own profile" ON public.profiles FOR SELECT TO authenticated USING (auth.uid() = id OR public.has_role(auth.uid(), 'admin'));
CREATE POLICY "Users insert own profile" ON public.profiles FOR INSERT TO authenticated WITH CHECK (auth.uid() = id);
CREATE POLICY "Users update own profile" ON public.profiles FOR UPDATE TO authenticated USING (auth.uid() = id OR public.has_role(auth.uid(), 'admin'));
CREATE POLICY "Admins delete profiles" ON public.profiles FOR DELETE TO authenticated USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Users read own roles" ON public.user_roles FOR SELECT TO authenticated USING (user_id = auth.uid() OR public.has_role(auth.uid(), 'admin'));

-- Auto-create profile + default role on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name, email)
  VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'full_name', ''), COALESCE(NEW.email, ''))
  ON CONFLICT (id) DO NOTHING;
  INSERT INTO public.user_roles (user_id, role) VALUES (NEW.id, 'engineer')
  ON CONFLICT (user_id, role) DO NOTHING;
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Devices
CREATE TABLE public.devices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  zone TEXT NOT NULL DEFAULT '',
  pipeline TEXT NOT NULL DEFAULT '',
  status public.device_status NOT NULL DEFAULT 'offline',
  battery INTEGER NOT NULL DEFAULT 100,
  signal INTEGER NOT NULL DEFAULT 0,
  firmware TEXT NOT NULL DEFAULT '',
  baseline_db NUMERIC NOT NULL DEFAULT 0,
  last_ping TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.devices TO authenticated;
GRANT ALL ON public.devices TO service_role;
ALTER TABLE public.devices ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Authenticated read devices" ON public.devices FOR SELECT TO authenticated USING (true);
CREATE POLICY "Staff insert devices" ON public.devices FOR INSERT TO authenticated WITH CHECK (public.has_role(auth.uid(), 'admin') OR public.has_role(auth.uid(), 'engineer'));
CREATE POLICY "Staff update devices" ON public.devices FOR UPDATE TO authenticated USING (public.has_role(auth.uid(), 'admin') OR public.has_role(auth.uid(), 'engineer'));
CREATE POLICY "Admins delete devices" ON public.devices FOR DELETE TO authenticated USING (public.has_role(auth.uid(), 'admin'));

-- Leak events
CREATE TABLE public.leak_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reference TEXT NOT NULL UNIQUE DEFAULT 'LK-' || upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 6)),
  device_id UUID REFERENCES public.devices(id) ON DELETE SET NULL,
  zone TEXT NOT NULL DEFAULT '',
  severity public.leak_severity NOT NULL DEFAULT 'medium',
  status public.leak_status NOT NULL DEFAULT 'active',
  confidence NUMERIC NOT NULL DEFAULT 0,
  acoustic_db NUMERIC NOT NULL DEFAULT 0,
  frequency_hz NUMERIC NOT NULL DEFAULT 0,
  estimated_loss_lpm NUMERIC NOT NULL DEFAULT 0,
  assigned_to UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.leak_events TO authenticated;
GRANT ALL ON public.leak_events TO service_role;
ALTER TABLE public.leak_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Authenticated read leaks" ON public.leak_events FOR SELECT TO authenticated USING (true);
CREATE POLICY "Staff insert leaks" ON public.leak_events FOR INSERT TO authenticated WITH CHECK (public.has_role(auth.uid(), 'admin') OR public.has_role(auth.uid(), 'engineer'));
CREATE POLICY "Staff update leaks" ON public.leak_events FOR UPDATE TO authenticated USING (public.has_role(auth.uid(), 'admin') OR public.has_role(auth.uid(), 'engineer'));
CREATE POLICY "Admins delete leaks" ON public.leak_events FOR DELETE TO authenticated USING (public.has_role(auth.uid(), 'admin'));

-- Sensor readings
CREATE TABLE public.sensor_readings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  device_id UUID NOT NULL REFERENCES public.devices(id) ON DELETE CASCADE,
  acoustic_db NUMERIC NOT NULL,
  frequency_hz NUMERIC,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX sensor_readings_recorded_at_idx ON public.sensor_readings (recorded_at DESC);
GRANT SELECT, INSERT, DELETE ON public.sensor_readings TO authenticated;
GRANT ALL ON public.sensor_readings TO service_role;
ALTER TABLE public.sensor_readings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Authenticated read readings" ON public.sensor_readings FOR SELECT TO authenticated USING (true);
CREATE POLICY "Staff insert readings" ON public.sensor_readings FOR INSERT TO authenticated WITH CHECK (public.has_role(auth.uid(), 'admin') OR public.has_role(auth.uid(), 'engineer'));
CREATE POLICY "Admins delete readings" ON public.sensor_readings FOR DELETE TO authenticated USING (public.has_role(auth.uid(), 'admin'));

-- Notifications
CREATE TABLE public.notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  message TEXT NOT NULL DEFAULT '',
  severity public.notification_severity NOT NULL DEFAULT 'info',
  read BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.notifications TO authenticated;
GRANT ALL ON public.notifications TO service_role;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own notifications" ON public.notifications FOR SELECT TO authenticated USING (user_id = auth.uid());
CREATE POLICY "Users insert own notifications" ON public.notifications FOR INSERT TO authenticated WITH CHECK (user_id = auth.uid());
CREATE POLICY "Users update own notifications" ON public.notifications FOR UPDATE TO authenticated USING (user_id = auth.uid());
CREATE POLICY "Users delete own notifications" ON public.notifications FOR DELETE TO authenticated USING (user_id = auth.uid());