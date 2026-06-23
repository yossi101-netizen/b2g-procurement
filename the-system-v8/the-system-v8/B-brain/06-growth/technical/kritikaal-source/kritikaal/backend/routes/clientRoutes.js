import express from "express";
import supabase from "../supabaseClient.js";
import { sendEmail } from "../services/emailService.js";
import { STAGE_NOTIFICATIONS } from "../utils/stageNotifications.js";

const router = express.Router();

// 2. GET ALL CLIENTS
router.get("/clients", async (req, res) => {
  try {
    const { data: clients, error } = await supabase
      .from("clients")
      .select("*")
      .eq("deleted", false)
      .order("created_at", { ascending: false });

    if (error) throw error;
    res.json({ success: true, data: clients });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 3. GET SINGLE CLIENT
router.get("/clients/:id", async (req, res) => {
  try {
    const { data: client, error } = await supabase
      .from("clients")
      .select("*")
      .eq("id", req.params.id)
      .single();

    if (error) throw error;
    res.json({ success: true, data: client });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 4. UPDATE STAGE
router.put("/clients/:id/stage", async (req, res) => {
  try {
    const { stage } = req.body;
    const { id } = req.params;

    const { data: client, error } = await supabase
      .from("clients")
      .update({ stage })
      .eq("id", id)
      .select()
      .single();

    if (error) throw error;

    // Log Notification & Send Email
    const templateData = STAGE_NOTIFICATIONS[stage];
    if (templateData) {
      const emailBody = templateData.template
        .replace("{firstName}", client.first_name)
        .replace("{company}", client.company || "your company");

      try {
        await sendEmail({
          to: client.email,
          subject: templateData.subject || "Stage Update",
          html: `<p>${emailBody}</p>`,
        });

        // Save Notification Log
        await supabase
          .from("notifications")
          .insert([{ type: "email", content: `Sent to ${client.email}: ${templateData.subject}`, client_id: id }]);

      } catch (emailErr) {
        console.error("Email send failed:", emailErr);
      }
    }

    res.json({ success: true, data: client });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 5. ADD NOTE
router.post("/clients/:id/notes", async (req, res) => {
  try {
    const { content } = req.body;
    const { data, error } = await supabase
      .from("notes")
      .insert([{ content, client_id: req.params.id }])
      .select()
      .single();

    if (error) throw error;
    res.status(201).json({ success: true, data });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 6. GET NOTES
router.get("/clients/:id/notes", async (req, res) => {
  try {
    const { data, error } = await supabase
      .from("notes")
      .select("*")
      .eq("client_id", req.params.id)
      .order("created_at", { ascending: false });

    if (error) throw error;
    res.json({ success: true, data });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 7. SOFT DELETE CLIENT
router.put("/clients/:id/delete", async (req, res) => {
  try {
    const { deleted_reason } = req.body;
    const { data, error } = await supabase
      .from("clients")
      .update({ deleted: true, deleted_reason })
      .eq("id", req.params.id)
      .select()
      .single();

    if (error) throw error;
    res.json({ success: true, data });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 8. PERMANENT DELETE
router.delete("/clients/:id", async (req, res) => {
  try {
    const { error } = await supabase
      .from("clients")
      .delete()
      .eq("id", req.params.id);

    if (error) throw error;
    res.json({ success: true, message: "Client deleted perfectly" });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 9. GET NOTIFICATION LOGS
router.get("/clients/:id/notifications", async (req, res) => {
  try {
    const { data, error } = await supabase
      .from("notifications")
      .select("*")
      .eq("client_id", req.params.id)
      .order("created_at", { ascending: false });

    if (error) throw error;
    res.json({ success: true, data });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 10. PIPELINE METRICS
router.get("/pipeline/metrics", async (req, res) => {
  try {
    const { data: clients, error } = await supabase
      .from("clients")
      .select("stage")
      .eq("deleted", false);

    if (error) throw error;

    const totalClients = clients.length;
    // Assuming you have deal_value or logic to calculate revenue
    const activeDeals = clients.filter(c => c.stage !== 'Closed Lost' && c.stage !== 'Closed Won').length;

    res.json({ 
      success: true, 
      data: {
        totalClients,
        activeDeals,
        totalRevenue: 0 // Fetch from deals/revenue schema when available
      }
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;