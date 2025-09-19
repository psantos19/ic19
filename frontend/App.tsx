import React, { useEffect, useState } from "react";
import { SafeAreaView, View, Text, Button, Alert } from "react-native";
import api from "./src/api/client";
import pt from "./src/api/i18n/pt";

type Rec = { slot_iso: string; eta_min: number; rank: number; chosen: boolean };

function splitAmPm(recs: Rec[]) {
  const am: Rec[] = [];
  const pm: Rec[] = [];
  recs.forEach(r => {
    const h = new Date(r.slot_iso).getHours();
    if (h < 12) am.push(r); else pm.push(r);
  });
  return { am, pm };
}

export default function App() {
  const [recs, setRecs] = useState<Rec[]>([]);
  const [loading, setLoading] = useState(false);
  const userId = 1; // stub
  const tomorrow = new Date(Date.now() + 24*60*60*1000).toISOString().slice(0,10);

  const load = () => {
    api.get(`/recommendations/${userId}`, { params: { date_str: tomorrow }})
      .then(r => setRecs(r.data))
      .catch(err => console.error(err));
  };

  useEffect(() => { load(); }, []);

  const accept = async (slot_iso: string) => {
    try {
      setLoading(true);
      await api.post(`/accept`, { user_id: userId, date: tomorrow, slot_iso });
      // feedback visual: marcar chosen localmente
      setRecs(prev => prev.map(x => x.slot_iso === slot_iso ? { ...x, chosen: true } : x));
      Alert.alert("✅ Guardado", "Recomendação aceite para esse horário.");
    } catch (e) {
      Alert.alert("Erro", "Não foi possível aceitar. Tenta novamente.");
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const { am, pm } = splitAmPm(recs);

  const Section = ({ title, data }: { title: string; data: Rec[] }) => (
    <View style={{ marginTop: 12 }}>
      <Text style={{ fontSize: 18, fontWeight: "600", marginBottom: 8 }}>{title}</Text>
      {data.length === 0 && <Text style={{ opacity: 0.6 }}>Sem sugestões.</Text>}
      {data.map((r) => (
        <View key={r.slot_iso} style={{ paddingVertical: 10, borderBottomWidth: 0.5, borderColor: "#ddd" }}>
          <Text>Hora: {new Date(r.slot_iso).toLocaleTimeString()}</Text>
          <Text>ETA: {r.eta_min} min {r.rank === 1 ? " · melhor" : ""}</Text>
          <Button
            title={r.chosen ? "Aceite ✅" : pt.aceitar}
            disabled={r.chosen || loading}
            onPress={() => accept(r.slot_iso)}
          />
        </View>
      ))}
    </View>
  );

  return (
    <SafeAreaView>
      <View style={{ padding: 16 }}>
        <Text style={{ fontSize: 22, fontWeight: "700", marginBottom: 8 }}>{pt.titulo}</Text>
        <Text style={{ marginBottom: 16 }}>Melhores opções para amanhã ({tomorrow}):</Text>
        <Section title="Manhã" data={am} />
        <Section title="Tarde" data={pm} />
      </View>
    </SafeAreaView>
  );
}
