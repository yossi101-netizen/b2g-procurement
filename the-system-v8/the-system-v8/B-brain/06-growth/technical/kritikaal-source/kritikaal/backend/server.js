import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import leadRoutes from './routes/leadRoutes.js';
import clientRoutes from './routes/clientRoutes.js';
import supabase from './supabaseClient.js';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(express.json());

// CORS configuration - Allow all origins for now to prevent frontend issues
app.use(cors());

// Test Route
app.get('/', (req, res) => {
  res.json({ message: 'KRITIKAAL CRM API is running' });
});

// Render Health Checks
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Healthy' });
});
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'KRITIKAAL Backend is running' });
});

// Configure Routes
app.use('/api', leadRoutes);
app.use('/api', clientRoutes);

// Start the server
app.listen(PORT, async () => {
  console.log(`Server is running on port ${PORT}`);
  
  // Verify Supabase Connection
  try {
    const { error } = await supabase.from('clients').select('id', { count: 'exact', head: true });
    if (error && error.code !== '42P01') { // 42P01 Table undefined is fine for connection check
       console.error("Supabase Error details:", error.message);
    } else {
       console.log("Supabase PostgreSQL Connected successfully");
    }
  } catch (error) {
    console.error("Supabase Connection Failed!", error);
  }
});

