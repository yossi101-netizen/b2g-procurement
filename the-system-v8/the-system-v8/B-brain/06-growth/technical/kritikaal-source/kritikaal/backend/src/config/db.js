import { supabase } from './supabaseClient.js';

const connectDB = async () => {
  try {
    const { error } = await supabase.from('clients').select('id', { count: 'exact', head: true });
    // If it's a 42P01 error, the database connected but the table doesn't exist yet. That's fine for connection check.
    if (error && error.code !== '42P01') {
      throw error;
    }
    console.log("Supabase Connection Successful");
  } catch (error) {
    console.error("Supabase Connection Failed! Please ensure your SUPABASE_URL and SUPABASE_ANON_KEY in .env are correct.");
    console.error("Error details:", error.message);
  }
};

export default connectDB;