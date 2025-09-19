import React, { useEffect, useState } from "react";
import { SafeAreaView, View, Text, Button } from "react-native";
import api from "./src/api/client";
import pt from "./src/i18n/pt";

export default function App() {
  const [recs, setRecs] = useState<any[]>([]);
  const userId = 1; // stub MVP
  const tomorrow = new Date(Date.now() + 24*60*60*1000).toISOString().slice(0,10);

  useEffect(() => {
    api.get(`/recommendations/${userId}`, { params: { date: tomorrow }})
      .then(r => setRecs(r.data))
      .catch(console.error);
  }, []);

  const accept = (slot_iso: string) => {
    api.post(`/accept`, { user_id: userId, date: tomorrow, slot_iso }).catch(console.error);
  };

  return (
    <SafeAreaView>
      <View style={{ padding: 16 }}>
        <Text style={{ fontSize: 22, fontWeight: "700", marginBottom: 8 }}>{pt.titulo}</Text>
        <Text style={{ marginBottom: 16 }}>Melhores opções para amanhã:</Text>
        {recs.map((r) => (
          <View key={r.slot_iso} style={{ paddingVertical: 12 }}>
            <Text>Hora: {new Date(r.slot_iso).toLocaleTimeString()}</Text>
            <Text>ETA: {r.eta_min} min</Text>
            <Button title={pt.aceitar} onPress={() => accept(r.slot_iso)} />
          </View>
        ))}
      </View>
    </SafeAreaView>
  );
}
