import React, { useEffect, useState } from "react";
import { SafeAreaView, View, Text, Button, Alert, ActivityIndicator } from "react-native";
import api from "./src/api/client";
// ajusta este import ao caminho que tens atualmente:
import pt from "./src/api/i18n/pt"; // se estavas a usar "./src/api/i18n/pt", mantém
import Onboarding from "./src/api/screens/Onboarding";
import { getUserId } from "./src/api/storage";
// import { saveUserId } from "../api/storage";

type Rec = { slot_iso: string; eta_min: number; rank: number; chosen: boolean };

function splitAmPm(recs: Rec[]) {
  const am: Rec[] = [], pm: Rec[] = [];
  recs.forEach(r => (new Date(r.slot_iso).getHours() < 12 ? am : pm).push(r));
  return { am, pm };
}

export default function App() {
  const [recs, setRecs] = useState<Rec[]>([]);
  const [loading, setLoading] = useState(false);
  const [uid, setUid] = useState<number | null>(null);
  const [booting, setBooting] = useState(true);

  const tomorrow = new Date(Date.now() + 24*60*60*1000).toISOString().slice(0,10);

  const load = (userId: number) =>
    api.get(`/recommendations/${userId}`, { params: { date_str: tomorrow }})
       .then(r => setRecs(r.data));

  useEffect(() => {
    const id = getUserId();
    setUid(id);
    if (id) load(id).finally(() => setBooting(false));
    else setBooting(false);
  }, []);

  const accept = async (slot_iso: string) => {
    if (!uid) return;
    try {
      setLoading(true);
      await api.post(`/accept`, { user_id: uid, date: tomorrow, slot_iso });
      setRecs(prev => prev.map(x => x.slot_iso === slot_iso ? { ...x, chosen: true } : x));
      Alert.alert("✅ Guardado", "Recomendação aceite para esse horário.");
    } catch {
      Alert.alert("Erro", "Não foi possível aceitar. Tenta novamente.");
    } finally {
      setLoading(false);
    }
  };

  if (booting) {
    return <SafeAreaView><View style={{padding:16}}><ActivityIndicator /><Text> a iniciar…</Text></View></SafeAreaView>;
  }

  if (!uid) {
    // não há utilizador → mostrar onboarding
    return <SafeAreaView><Onboarding onDone={() => {
      const id = getUserId();
      setUid(id);
      if (id) load(id);
    }} /></SafeAreaView>;
  }

  const { am, pm } = splitAmPm(recs);

  const Section = ({ title, data }: { title: string; data: Rec[] }) => (
    <View style={{ marginTop: 12 }}>
      <Text style={{ fontSize: 18, fontWeight: "600", marginBottom: 8 }}>{title}</Text>
      {data.length === 0 && <Text style={{ opacity: 0.6 }}>{pt.sem_sugestoes ?? "Sem sugestões."}</Text>}
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
        <Section title={pt.manha ?? "Manhã"} data={am} />
        <Section title={pt.tarde ?? "Tarde"} data={pm} />
      </View>
    </SafeAreaView>
  );
}
