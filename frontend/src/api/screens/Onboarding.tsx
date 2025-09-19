import React, { useState } from "react";
import { View, Text, TextInput, Button, Alert, Platform } from "react-native";
import api from "../client";
import { saveUserId } from "../storage";
import MapSelect from "./MapSelect";

type Point = { lat: number; lng: number; label?: string };

export default function Onboarding({ onDone }: { onDone: () => void }) {
  const [home, setHome] = useState("Sintra-Noroeste");
  const [work, setWork] = useState("Lisboa-Centro");
  const [flexMinus, setFlexMinus] = useState("10");
  const [flexPlus, setFlexPlus] = useState("20");
  const [employer, setEmployer] = useState("");

  const [showMap, setShowMap] = useState(false);
  const [origin, setOrigin] = useState<Point | null>(null);
  const [destination, setDestination] = useState<Point | null>(null);

  const submit = async () => {
    try {
      const preferences = {
        origin,
        destination,
      };
      const body = {
        home_zone: origin?.label || home,
        work_zone: destination?.label || work,
        flex_minus_min: Number(flexMinus) || 0,
        flex_plus_min: Number(flexPlus) || 0,
        employer_name: employer || null,
        // vamos enviar o objeto inteiro no preferences_json
        // (o backend já tem este campo)
        preferences_json: preferences,
      };
      const res = await api.post("/signup", body);
      const id = res.data?.user_id;
      if (id) {
        saveUserId(id);
        Alert.alert("✅ Conta criada", "Recomendações serão geradas para amanhã.");
        onDone();
      } else {
        Alert.alert("Erro", "Resposta inesperada do servidor.");
      }
    } catch (e) {
      console.error(e);
      Alert.alert("Erro", "Não foi possível criar a conta. Tenta mais tarde.");
    }
  };

  if (showMap) {
    return (
      <MapSelect
        initialOrigin={origin}
        initialDestination={destination}
        onConfirm={(o, d) => {
          setOrigin(o); setDestination(d); setShowMap(false);
          if (o?.label) setHome(o.label);
          if (d?.label) setWork(d.label);
        }}
        onCancel={() => setShowMap(false)}
      />
    );
  }

  const Box = ({label, value, onChangeText, keyboardType="default"}: any) => (
    <View style={{ marginVertical: 6 }}>
      <Text style={{ fontWeight: "600" }}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        keyboardType={keyboardType}
        placeholder="Escreve aqui…"
        style={{ borderWidth: 1, borderColor: "#ccc", borderRadius: 6, padding: 8 }}
      />
    </View>
  );

  return (
    <View style={{ padding: 16 }}>
      <Text style={{ fontSize: 22, fontWeight: "700", marginBottom: 12 }}>Bem-vindo 👋</Text>
      <Text style={{ marginBottom: 12 }}>Define a tua rotina para personalizarmos as horas de saída.</Text>

      <Box label="Zona/Bairro de origem" value={home} onChangeText={setHome} />
      <Box label="Zona/Bairro de destino" value={work} onChangeText={setWork} />

      <View style={{ marginVertical: 8 }}>
        <Button title={Platform.OS === "web" ? "Definir no mapa (mobile)" : "Definir no mapa"} onPress={() => setShowMap(true)} />
      </View>

      <Box label="Flexibilidade (minutos antes)" value={flexMinus} onChangeText={setFlexMinus} keyboardType="numeric" />
      <Box label="Flexibilidade (minutos depois)" value={flexPlus} onChangeText={setFlexPlus} keyboardType="numeric" />
      <Box label="Empresa (opcional)" value={employer} onChangeText={setEmployer} />

      <View style={{ marginTop: 12 }}>
        <Button title="Guardar" onPress={submit} />
      </View>
    </View>
  );
}
