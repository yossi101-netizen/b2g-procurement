"use client";

import { useState, useMemo, useEffect } from "react";
import { Calendar } from "@/components/ui/calendar";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CalendarDays, Clock, Globe, Check, Loader2 } from "lucide-react";
import { format, isSaturday, isSunday, startOfDay } from "date-fns";
import { useTranslation } from "@/contexts/TranslationContext";

// Helper to handle missing translations safely
const getCountryName = (t: (key: string) => string, key: string, fallback: string) => {
  const translated = t(key);
  return translated === key ? fallback : translated;
};

// Timezone data
const getTimezones = (t: (key: string) => string) => [
  { country: getCountryName(t, 'bookACallPage.india', 'India'), code: "IN", tz: "Asia/Kolkata", offset: 0, label: "IST (UTC+5:30)" },
  { country: getCountryName(t, 'bookACallPage.netherlands', 'Netherlands'), code: "NL", tz: "Europe/Amsterdam", offset: 1, label: "CET (UTC+1:00)" },
  { country: getCountryName(t, 'bookACallPage.france', 'France'), code: "FR", tz: "Europe/Paris", offset: 1, label: "CET (UTC+1:00)" },
  { country: getCountryName(t, 'bookACallPage.germany', 'Germany'), code: "DE", tz: "Europe/Berlin", offset: 1, label: "CET (UTC+1:00)" },
  { country: getCountryName(t, 'bookACallPage.italy', 'Italy'), code: "IT", tz: "Europe/Rome", offset: 1, label: "CET (UTC+1:00)" },
  { country: getCountryName(t, 'bookACallPage.unitedKingdom', 'United Kingdom'), code: "GB", tz: "Europe/London", offset: 0, label: "GMT (UTC+0:00)" },
  { country: getCountryName(t, 'bookACallPage.spain', 'Spain'), code: "ES", tz: "Europe/Madrid", offset: 1, label: "CET (UTC+1:00)" },
  { country: getCountryName(t, 'bookACallPage.israel', 'Israel'), code: "IL", tz: "Asia/Jerusalem", offset: 2, label: "Israel Time (UTC+2:00)" },
  { country: getCountryName(t, 'bookACallPage.unitedStatesEST', 'United States'), code: "US-EST", tz: "America/New_York", offset: -5, label: "EST (UTC-5:00)" },
  { country: getCountryName(t, 'bookACallPage.unitedStatesPST', 'United States'), code: "US-PST", tz: "America/Los_Angeles", offset: -8, label: "PST (UTC-8:00)" }, 
  { country: getCountryName(t, 'bookACallPage.uae', 'United Arab Emirates'), code: "AE", tz: "Asia/Dubai", offset: 4, label: "GST (UTC+4:00)" }
];

// Generate time slots from 10:00 AM to 8:00 PM
const generateTimeSlots = () => {
  const slots: { time: string; hour: number; minute: number }[] = [];
  let hour = 10;
  let minute = 0;

  while (hour < 20 || (hour === 20 && minute === 0)) {
    const period = hour >= 12 ? "PM" : "AM";
    const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    const displayMinute = minute.toString().padStart(2, "0");
    slots.push({
      time: `${displayHour}:${displayMinute} ${period}`,
      hour,
      minute,
    });

    minute += 30;
    if (minute >= 60) {
      minute = 0;
      hour += 1;
    }
  }
  return slots;
};

const timeSlots = generateTimeSlots();

const countryPhoneMap: Record<string, string> = {
  "United Kingdom": "+44",
  "United States": "+1",
  "Spain": "+34",
  "United Arab Emirates": "+971",
  "Netherlands": "+31",
  "France": "+33",
  "Germany": "+49",
  "Italy": "+39",
  "India": "+91",
  "Israel": "+972",
};

export const BookACall = () => {
  const { t } = useTranslation();
  const timezones = useMemo(() => getTimezones(t), [t]);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);
  const [selectedTime, setSelectedTime] = useState<string | undefined>(undefined);
  const [selectedTimezone, setSelectedTimezone] = useState<string>("IN");
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    company: "",
    country: "",
    phoneCode: "+1",
    phone: "",
    email: "",
    leatherDesign: "",
    message: "",
  });
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [submissionData, setSubmissionData] = useState<{
    name: string;
    timestamp: Date;
  } | null>(null);
  const [dynamicCountry, setDynamicCountry] = useState<{name: string, code: string, phoneCode: string} | null>(null);

  useEffect(() => {
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
      let detectedCode = "IN"; // Default fallback
      let initialCountry = "India";

      if (tz.includes("Kolkata") || tz.includes("Calcutta")) { detectedCode = "IN"; initialCountry = "India"; }
      else if (tz.includes("Amsterdam")) { detectedCode = "NL"; initialCountry = "Netherlands"; }
      else if (tz.includes("Paris")) { detectedCode = "FR"; initialCountry = "France"; }
      else if (tz.includes("Berlin") || tz.includes("Busingen")) { detectedCode = "DE"; initialCountry = "Germany"; }
      else if (tz.includes("Rome") || tz.includes("Vatican")) { detectedCode = "IT"; initialCountry = "Italy"; }
      else if (tz.includes("London") || tz.includes("Belfast")) { detectedCode = "GB"; initialCountry = "United Kingdom"; }
      else if (tz.includes("Madrid") || tz.includes("Ceuta") || tz.includes("Canary")) { detectedCode = "ES"; initialCountry = "Spain"; }
      else if (tz.includes("New_York") || tz.includes("Detroit") || tz.includes("Indiana") || tz.includes("Chicago") || tz.includes("Eastern") || tz.includes("Central")) { detectedCode = "US-EST"; initialCountry = "United States"; }
      else if (tz.includes("Los_Angeles") || tz.includes("Denver") || tz.includes("Boise") || tz.includes("Phoenix") || tz.includes("Pacific") || tz.includes("Mountain")) { detectedCode = "US-PST"; initialCountry = "United States"; }
      else if (tz.includes("Dubai")) { detectedCode = "AE"; initialCountry = "United Arab Emirates"; }
      else if (tz.includes("Jerusalem") || tz.includes("Tel_Aviv") || tz.includes("Israel")) { detectedCode = "IL"; initialCountry = "Israel"; }

      setSelectedTimezone(detectedCode);
      setFormData(prev => ({ 
        ...prev, 
        country: initialCountry, 
        phoneCode: countryPhoneMap[initialCountry] || prev.phoneCode 
      }));

      // Async fallback to IP-based country detection for better accuracy
      fetch("https://ipapi.co/json/")
        .then((res) => res.json())
        .then((data) => {
          if (data && data.country_code) {
            const cc = data.country_code;
            let ipCountryCode = detectedCode;
            let ipCountryName = initialCountry;

            const countryNameMap: Record<string, string> = {
              "IN": "India", "NL": "Netherlands", "FR": "France", "DE": "Germany",
              "IT": "Italy", "GB": "United Kingdom", "ES": "Spain", "AE": "United Arab Emirates", "IL": "Israel"
            };

            if (["NL", "FR", "DE", "IT", "GB", "ES", "AE", "IN", "IL"].includes(cc)) {
              ipCountryCode = cc;
              ipCountryName = countryNameMap[cc];
            } else if (cc === "US") {
              ipCountryName = "United States";
              const tzName = data.timezone || "";
              if (
                tzName.includes("Los_Angeles") ||
                tzName.includes("Denver") ||
                tzName.includes("Phoenix") ||
                tzName.includes("Boise")
              ) {
                ipCountryCode = "US-PST";
              } else {
                ipCountryCode = "US-EST";
              }
            } else {
              ipCountryName = data.country_name;
              setDynamicCountry({ name: data.country_name, code: cc, phoneCode: data.country_calling_code || "+1" });
            }
            
            setSelectedTimezone(ipCountryCode);
            setFormData(prev => ({ 
              ...prev, 
              country: ipCountryName, 
              phoneCode: countryPhoneMap[ipCountryName] || data.country_calling_code || prev.phoneCode 
            }));
          }
        })
        .catch((err) => {
          console.log("IP-based detection failed. Using Intl Timezone.", err);
        });
    } catch (e) {
      console.log("Timezone detection failed", e);
    }
  }, []);

  // Backend API URL - will use environment variable after deployment
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

  const currentTimezone = timezones.find(tz => tz.code === selectedTimezone) || timezones[0];

  // Disable weekends and past dates
  const disabledDays = (date: Date) => {
    const today = startOfDay(new Date());
    const checkDate = startOfDay(date);
    return isSaturday(date) || isSunday(date) || checkDate < today;
  };

  const formatSlotTime = (hour: number, minute: number) => {
    const p = hour >= 12 ? "PM" : "AM";
    const h = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    const m = minute.toString().padStart(2, "0");
    return `${h}:${m} ${p}`;
  };

  const getAvailableTimeSlots = () => {
    if (!selectedDate) return timeSlots;

    return timeSlots.filter(slot => {
      const year = selectedDate.getFullYear();
      const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
      const date = String(selectedDate.getDate()).padStart(2, '0');
      const hour = String(slot.hour).padStart(2, '0');
      const minute = String(slot.minute).padStart(2, '0');
      
      // Use local timezone string without +05:30 to validate against user's local real time
      const dateString = `${year}-${month}-${date}T${hour}:${minute}:00`;
      const slotDate = new Date(dateString);
      
      return slotDate > new Date();
    });
  };

  const handleDateSelect = (date: Date | undefined) => {
    setSelectedDate(date);
    if (date) {
      setStep(2);
    }
  };

  const handleTimeSelect = (time: string) => {
    setSelectedTime(time);
    setStep(3);
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    // Validate dropdowns (Select fields) manually since they don't use native HTML required attribute
    if (!formData.country) {
      setErrorMessage("Please select a Country.");
      return;
    }
    if (!formData.leatherDesign) {
      setErrorMessage("Please select a Leather Design.");
      return;
    }

    setLoading(true);

    let finalPreferredTime = selectedTime || "Not specified";
    if (selectedDate && selectedTime) {
      if (currentTimezone && currentTimezone.code !== "IN") {
        finalPreferredTime = `${selectedTime} (${currentTimezone.label}) / Local Time`;
      } else {
        finalPreferredTime = `${selectedTime} (India Time)`;
      }
    }

    try {
      const response = await fetch(`${API_URL}/api/leads`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          firstName: formData.firstName,
          lastName: formData.lastName,
          company: formData.company,
          country: formData.country,
          email: formData.email,
          phone: formData.phone ? `${formData.phoneCode} ${formData.phone}` : "",
          leatherDesign: formData.leatherDesign,
          preferredDate: selectedDate ? format(selectedDate, 'yyyy-MM-dd') : "Not specified",
          preferredTime: finalPreferredTime,
          message: formData.message || "Book a call request",
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.error || "Failed to submit booking");
      }

      // Store submission data for thank-you page
      setSubmissionData({
        name: `${formData.firstName} ${formData.lastName}`.trim(),
        timestamp: new Date()
      });
      setSuccessMessage(t('bookACallPage.successMessage'));
      setFormData({ firstName: "", lastName: "", company: "", country: "", phoneCode: "+1", phone: "", email: "", leatherDesign: "", message: "" });
      setSelectedDate(undefined);
      setSelectedTime(undefined);
      setStep(1);
    } catch (error) {
      console.error("Booking error:", error);
      setErrorMessage(error instanceof Error ? error.message : t('bookACallPage.errorMessage'));
    } finally {
      setLoading(false);
    }
  };

  if (successMessage) {
    return (
      <section className="py-24 sm:py-16 md:py-24 bg-warm-beige">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="max-w-3xl mx-auto">
            {/* Success Icon and Message */}
            <div className="text-center mb-8">
              <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
                <Check className="w-10 h-10 sm:w-12 sm:h-12 text-green-600" />
              </div>
              <h2 className="font-serif text-2xl sm:text-3xl text-charcoal mb-4">
                {t('bookACallPage.requestSubmitted')}
              </h2>
              <div className="bg-green-50 border border-green-200 text-green-800 px-6 py-4 rounded-lg mb-6">
                <p className="font-medium">{successMessage}</p>
              </div>
            </div>

            {/* Thank You Section with Dynamic User Info */}
            {submissionData && (
              <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8 mb-8">
                <h3 className="font-serif text-xl sm:text-2xl text-charcoal mb-4 text-center">
                  Thank You, <span className="text-saddle-tan">{submissionData.name}</span>!
                </h3>
                <p className="text-charcoal/70 text-center mb-6">
                  Your booking request was submitted on{" "}
                  <span className="font-serif font-normal text-charcoal">
                    {format(submissionData.timestamp, "MMMM d, yyyy 'at' h:mm a")}
                  </span>
                </p>

                {/* Video Player Section */}
                <div className="mt-8">
                  <h4 className="font-serif text-lg sm:text-xl text-charcoal mb-4 text-center">
                    Learn More About Our Craftsmanship
                  </h4>
                  <div className="relative w-full aspect-video bg-charcoal/5 rounded-lg overflow-hidden shadow-md hover:shadow-xl transition-shadow duration-300">
                    <video
                      controls
                      className="w-full h-full object-cover cursor-pointer"
                      poster="/leather-bg.avif"
                    >
                      <source src="/video/craftsmanship.mp4" type="video/mp4" />
                      <source src="/video/craftsmanship.webm" type="video/webm" />
                      Your browser does not support the video tag.
                    </video>
                  </div>
                  <p className="text-xs sm:text-sm text-charcoal/60 text-center mt-3">
                    Click to watch our artisans at work
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="py-24 bg-warm-beige">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <span className="text-saddle-tan font-medium tracking-widest uppercase text-xs sm:text-sm">
            {t('bookACallPage.scheduleMeeting')}
          </span>
          <h2 className="font-serif text-2xl sm:text-3xl md:text-4xl lg:text-5xl text-charcoal mt-3 sm:mt-4 mb-4 sm:mb-6">
            {t('bookACallPage.title')} <span className="text-saddle-tan">{t('bookACallPage.titleHighlight')}</span>
          </h2>
          <p className="text-charcoal/70 max-w-2xl mx-auto text-sm sm:text-base">
            {t('bookACallPage.consultationDesc')}
          </p>
        </div>

        {/* Timezone Selector */}
        <div className="max-w-md mx-auto mb-6 sm:mb-8">
          <Label className="flex items-center gap-2 mb-2 text-xs sm:text-sm text-charcoal/70">
            <Globe className="w-4 h-4" />
            {t('bookACallPage.selectTimezone')}
          </Label>
          <Select 
            value={selectedTimezone} 
            onValueChange={(val) => {
              setSelectedTimezone(val);
              const tz = timezones.find(t => t.code === val);
              if (tz) {
                 const countryName = tz.country;
                 setFormData(prev => ({
                   ...prev,
                   country: countryName,
                   phoneCode: countryPhoneMap[countryName] || prev.phoneCode
                 }));
              }
            }}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder={t('bookACallPage.selectTimezonePlaceholder')} />
            </SelectTrigger>
            <SelectContent>
              {timezones.map((tz) => (
                <SelectItem key={tz.code} value={tz.code}>
                  {tz.country} — {tz.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Progress Steps */}
        <div className="flex justify-center items-center gap-4 mb-12">
          {[
            { num: 1, label: t('bookACallPage.step1') },
            { num: 2, label: t('bookACallPage.step2') },
            { num: 3, label: t('bookACallPage.step3') },
          ].map((s, index) => (
            <div key={s.num} className="flex items-center">
              <div
                onClick={() => {
                  if (s.num === 1) setStep(1);
                  if (s.num === 2 && selectedDate) setStep(2);
                  if (s.num === 3 && selectedDate && selectedTime) setStep(3);
                }}
                className={`flex items-center justify-center w-10 h-10 rounded-full font-serif font-normal transition-all cursor-pointer ${
                  step >= s.num
                    ? "bg-saddle-tan text-white"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {step > s.num ? <Check className="w-5 h-5" /> : s.num}
              </div>
              <span
                className={`ml-1 sm:ml-2 text-xs sm:text-sm hidden xs:inline ${
                  step >= s.num ? "text-charcoal" : "text-gray-500"
                }`}
              >
                {s.label}
              </span>
              {index < 2 && (
                <div
                  className={`w-4 sm:w-8 md:w-16 h-0.5 mx-1 sm:mx-2 md:mx-4 ${
                    step > s.num ? "bg-saddle-tan" : "bg-gray-200"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Booking Interface */}
        <div className="max-w-4xl mx-auto">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Calendar Card */}
            <Card className="border-charcoal/10 shadow-lg w-full">
  <CardHeader className="pb-2 sm:pb-4 text-center">
    <CardTitle className="flex items-center justify-center gap-2 font-serif text-lg sm:text-xl text-charcoal">
      <CalendarDays className="w-5 h-5 text-saddle-tan" />
      {t('bookACallPage.selectDate')}
    </CardTitle>
  </CardHeader>

  <CardContent className="p-4 flex flex-col items-center">
    
    {/* Calendar Wrapper */}
    <div className="w-full max-w-md mx-auto flex justify-center">
      <Calendar
        mode="single"
        selected={selectedDate}
        onSelect={handleDateSelect}
        disabled={disabledDays}
        className="w-full rounded-md border-0 p-2"
        classNames={{
          months: "w-full flex justify-center",
          month: "w-full",
          table: "w-full",
          head_row: "flex justify-between",
          row: "flex justify-between w-full",
          cell: "flex-1 text-center",

          day: "w-10 h-10 flex items-center justify-center mx-auto",
          day_selected:
            "!bg-saddle-tan !text-white hover:!bg-saddle-tan hover:!text-white focus:!bg-saddle-tan focus:!text-white",
          day_today: "bg-warm-beige text-charcoal",
        }}
      />
    </div>

    <p className="text-xs text-charcoal/60 mt-4 text-center">
      {t('bookACallPage.weekendsNotAvailable')}
    </p>

  </CardContent>
</Card>

            {/* Time Slots / Form Card */}
            {step === 1 && (
              <Card className="border-charcoal/10 shadow-lg h-full flex items-center justify-center">
                <CardContent className="text-center py-12">
                  <CalendarDays className="w-12 h-12 text-charcoal/30 mx-auto mb-4" />
                  <p className="text-charcoal/60">
                    {t('bookACallPage.selectDateFirst')}
                  </p>
                </CardContent>
              </Card>
            )}

            {step === 2 && selectedDate && (
              <Card className="border-charcoal/10 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 font-serif text-xl text-charcoal">
                    <Clock className="w-5 h-5 text-saddle-tan" />
                    {t('bookACallPage.availableTimes')}
                  </CardTitle>
                  <p className="text-sm text-charcoal/70">
                    {format(selectedDate, "EEEE, MMMM d, yyyy")}
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-2 max-h-[320px] overflow-y-auto pr-2">
                    {getAvailableTimeSlots().length > 0 ? (
                      getAvailableTimeSlots().map((slot) => (
                        <Button
                          key={slot.time}
                          variant={selectedTime === slot.time ? "default" : "outline"}
                          size="sm"
                          className={`text-xs ${
                            selectedTime === slot.time
                              ? "bg-saddle-tan hover:bg-saddle-tan/90 text-white"
                              : "hover:bg-saddle-tan/10"
                          }`}
                          onClick={() => handleTimeSelect(slot.time)}
                        >
                          {formatSlotTime(slot.hour, slot.minute)}
                        </Button>
                      ))
                    ) : (
                      <div className="col-span-2 text-center text-sm text-charcoal/60 py-4">
                        No more time slots available for today.
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-charcoal/60 mt-4 text-center">
                    All times are shown in {currentTimezone.label}
                  </p>
                </CardContent>
              </Card>
            )}

            {step === 3 && selectedDate && selectedTime && (
              <Card className="border-charcoal/10 shadow-lg">
                <CardHeader>
                  <CardTitle className="font-serif text-xl text-charcoal">
                    {t('bookACallPage.yourDetails')}
                  </CardTitle>
                  <p className="text-sm text-charcoal/70">
                    {format(selectedDate, "EEEE, MMMM d")} {t('bookACallPage.at')} {(() => {
                      const st = timeSlots.find(s => s.time === selectedTime);
                      return st ? formatSlotTime(st.hour, st.minute) : selectedTime;
                    })()}
                  </p>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="firstName">First Name *</Label>
                        <Input
                          id="firstName"
                          name="firstName"
                          value={formData.firstName}
                          onChange={handleInputChange}
                          required
                          disabled={loading}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="lastName">Last Name *</Label>
                        <Input
                          id="lastName"
                          name="lastName"
                          value={formData.lastName}
                          onChange={handleInputChange}
                          required
                          disabled={loading}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="company">Company *</Label>
                      <Input
                        id="company"
                        name="company"
                        value={formData.company}
                        onChange={handleInputChange}
                        required
                        disabled={loading}
                      />
                    </div>

                      <div className="space-y-2">
                        <Label htmlFor="country">Country *</Label>
                        <Select 
                          value={formData.country} 
                          onValueChange={(val) => 
                            setFormData(prev => ({ 
                              ...prev, 
                              country: val,
                              phoneCode: countryPhoneMap[val] || (dynamicCountry?.name === val ? dynamicCountry.phoneCode : prev.phoneCode) 
                            }))
                          }
                          disabled={loading}
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="🌍 Select Country" />
                          </SelectTrigger>
                          <SelectContent>
                            {dynamicCountry && !Object.keys(countryPhoneMap).includes(dynamicCountry.name) && (
                              <SelectItem value={dynamicCountry.name}>📍 {dynamicCountry.name}</SelectItem>
                            )}
                            <SelectItem value="United Kingdom">🇬🇧 United Kingdom</SelectItem>
                            <SelectItem value="United States">🇺🇸 United States</SelectItem>
                            <SelectItem value="Spain">🇪🇸 Spain</SelectItem>
                            <SelectItem value="United Arab Emirates">🇦🇪 United Arab Emirates</SelectItem>
                            <SelectItem value="Netherlands">🇳🇱 Netherlands</SelectItem>
                            <SelectItem value="France">🇫🇷 France</SelectItem>
                            <SelectItem value="Germany">🇩🇪 Germany</SelectItem>
                            <SelectItem value="Italy">🇮🇹 Italy</SelectItem>
                            <SelectItem value="India">🇮🇳 India</SelectItem>
                            <SelectItem value="Israel">🇮🇱 Israel</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                     <div className="space-y-2">
                       <Label htmlFor="phone">Phone *</Label>
                      <div className="flex items-center gap-3 w-full">
   {/* Phone Code */}
    <Select
      value={formData.phoneCode}
      onValueChange={(val) => {
        const countryName = Object.keys(countryPhoneMap).find(key => countryPhoneMap[key] === val);
        if (countryName) {
           setFormData((prev) => ({ ...prev, phoneCode: val, country: countryName }));
        } else {
           setFormData((prev) => ({ ...prev, phoneCode: val }));
        }
      }}
      disabled={loading}
    >
      <SelectTrigger className="h-11 w-[110px] shrink-0 px-2 text-center bg-transparent">
        <SelectValue placeholder="+1" />
      </SelectTrigger>

      <SelectContent>
        {dynamicCountry && !["+44", "+1", "+34", "+971", "+31", "+33", "+49", "+39", "+91", "+972"].includes(dynamicCountry.phoneCode) && (
          <SelectItem value={dynamicCountry.phoneCode}>{dynamicCountry.phoneCode} ({dynamicCountry.code})</SelectItem>
        )}
        <SelectItem value="+44">+44 (UK)</SelectItem>
        <SelectItem value="+1">+1 (US)</SelectItem>
        <SelectItem value="+34">+34 (ES)</SelectItem>
        <SelectItem value="+971">+971 (AE)</SelectItem>
        <SelectItem value="+31">+31 (NL)</SelectItem>
        <SelectItem value="+33">+33 (FR)</SelectItem>
        <SelectItem value="+49">+49 (DE)</SelectItem>
        <SelectItem value="+39">+39 (IT)</SelectItem>
        <SelectItem value="+91">+91 (IN)</SelectItem>
        <SelectItem value="+972">+972 (IL)</SelectItem>
      </SelectContent>
    </Select>

    {/* Phone Number */}
    <Input
      id="phone"
      name="phone"
      type="tel"
      value={formData.phone}
      onChange={(e) => {
        let val = e.target.value.replace(/\D/g, ""); // Allow only digits
        
        let maxLength = 10; // Default max length
        if (formData.country === "United Kingdom") maxLength = 11;
        else if (formData.country === "United States") maxLength = 10;
        else if (formData.country === "Spain") maxLength = 9;
        else if (formData.country === "United Arab Emirates") maxLength = 9;
        else if (formData.country === "Netherlands") maxLength = 9;
        else if (formData.country === "France") maxLength = 9;
        else if (formData.country === "Germany") maxLength = 11; // Can be 10 or 11
        else if (formData.country === "Italy") maxLength = 10; // Can vary
        else if (formData.country === "India") maxLength = 10;
        else if (formData.country === "Israel") maxLength = 9;
        
        if (val.length > maxLength) val = val.slice(0, maxLength);
        handleInputChange({ target: { name: "phone", value: val } } as any);
      }}
      placeholder="Enter phone number"
      required
      disabled={loading}
      className="h-11 flex-1 w-full bg-transparent"
    />
  </div>
</div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="email">Email *</Label>
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          value={formData.email}
                          onChange={handleInputChange}
                          required
                          disabled={loading}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="leatherDesign">Leather Design *</Label>
                        <Select 
                          value={formData.leatherDesign} 
                          onValueChange={(val) => setFormData(prev => ({ ...prev, leatherDesign: val }))}
                          disabled={loading}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select Design" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Bags">Bags</SelectItem>
                            <SelectItem value="Belts">Belts</SelectItem>
                            <SelectItem value="Wallets">Wallets</SelectItem>
                            <SelectItem value="Other">Other</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="message">Message</Label>
                      <Textarea
                        id="message"
                        name="message"
                        value={formData.message}
                        onChange={handleInputChange}
                        placeholder={t('bookACallPage.messagePlaceholder') || "Tell us about your project..."}
                        rows={3}
                        disabled={loading}
                      />
                    </div>
                    
                    {errorMessage && (
                      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                        {errorMessage}
                      </div>
                    )}
                    
                    <Button 
                      type="submit" 
                      className="w-full bg-saddle-tan hover:bg-saddle-tan/90"
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          {t('bookACallPage.sending')}
                        </>
                      ) : (
                        t('bookACallPage.confirmBooking')
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Selected Summary */}
          {(selectedDate || selectedTime) && step < 3 && (
            <div className="mt-8 p-4 bg-white rounded-xl text-center shadow-sm">
              <p className="text-sm text-charcoal/70">
                {t('bookACallPage.selected')}{" "}
                <span className="font-medium text-charcoal">
                  {selectedDate && format(selectedDate, "MMMM d, yyyy")}
                  {selectedTime && ` ${t('bookACallPage.at')} ${selectedTime}`}
                </span>
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default BookACall;

