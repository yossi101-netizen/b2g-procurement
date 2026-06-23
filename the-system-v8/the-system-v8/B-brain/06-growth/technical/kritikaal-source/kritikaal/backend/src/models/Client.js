import { supabase } from '../config/supabaseClient.js';

class Client {
  static async create(data) {
    const { data: client, error } = await supabase
      .from('clients')
      .insert(data)
      .select()
      .single();

    if (error) {
      console.error(error);
      throw new Error(error.message);
    }
    return client;
  }

  static find() {
    return {
      sort: async (condition) => {
        const orderBy = Object.keys(condition)[0];
        const ascending = condition[orderBy] === 1;
        const { data: clients, error } = await supabase
          .from('clients')
          .select('*')
          .order(orderBy, { ascending });
        
        if (error) throw new Error(error.message);
        
        // Mocking toObject and adding the id explicitly
        return clients.map(c => ({
          ...c,
          _id: c.id,
          toObject: function() { return this; }
        }));
      }
    };
  }

  static async findById(id) {
    const { data: client, error } = await supabase
      .from('clients')
      .select('*')
      .eq('id', id)
      .single();

    if (error || !client) {
      if (error && error.code === 'PGRST116') return null; // No rows found
      throw new Error(error?.message || 'Not found');
    }
    
    return {
      ...client,
      _id: client.id,
      toObject: function() { return this; }
    };
  }
}

export default Client;