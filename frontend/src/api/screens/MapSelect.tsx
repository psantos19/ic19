import React, { useEffect, useState } from "react";
import { View, Text, Button, Platform, TextInput, Alert } from "react-native";
import * as Location from "expo-location";

// Só importamos react-native-maps se não for web (para evitar erros no browser)
let MapView: any = null;
let Marker: any = null;
if (Platform.OS !== "web") {
  const maps = require("react-native-maps");
  MapView = maps.default;
  Marker = maps.Marker;
}

type Point = { lat: number; lng: number; label?: string };

export default function MapSelect({
  initialOrigin,
  initialDestination,
  onConfirm,
  onCancel,
}: {
  initialOrigin?: Point | null;
  initialDestination?: Point | null;
  onConfirm: (o: Point, d: Point) => void;
  onCancel: () => void;
}) {
  // Fallback sem mapa (web): inputs de texto
  const [origemLabel, setOrigemLabel] = useState(initialOrigin?.label ?? "");
  const [destinoLabel, setDestinoLabel] = useState(initialDestination?.label ?? "");

  // Mobile: markers arrastáveis
  const [origin, setOrigin] = useState<Point | null>(initialOrigin ?? null);
  const [destination, setDestination] = useState<Point | null>(initialDestination ?? null);
  const [region, setRegion] = useState({
    latitude: initialOrigin?.lat ?? 38.757, // zona Grande Lisboa
    longitude: initialOrigin?.lng ?? -9.18,
    latitudeDelta: 0.25,
    longitudeDelta: 0.25,
  });

  useEffect(() => {
    if (Platform.OS === "web") return;
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status === "granted") {
          const loc = await Location.getCurrentPositionAsync({});
          setRegion((r) => ({
            ...r,
            latitude: loc.coords.latitude,
            longitude: loc.coords.longitude,
            latitudeDelta: 0.1,
            longitudeDelta: 0.1,
          }));
          if (!origin) {
            setOrigin({ lat: loc.coords.latitude, lng: loc.coords.longitude, label: "Minha localização" });
          }
        }
      } catch {}
    })();
  }, []);

  const confirm = () => {
    if (Platform.OS === "web") {
      if (!origemLabel || !destinoLabel) {
        Alert.alert("Dados em falta", "Preenche origem e destino.");
        return;
      }
      // Como fallback, mandamos labels; o backend pode tratar como zonas textuais
      onConfirm(
        { lat: 0, lng: 0, label: origemLabel },
        { lat: 0, lng: 0, label: destinoLabel }
      );
      return;
    }
    if (!origin || !destination) {
      Alert.alert("Dados em falta", "Coloca os dois marcadores (origem e destino).");
      return;
    }
    onConfirm(origin, destination);
  };

  if (Platform.OS === "web" || !MapView) {
    // Fallback sem mapa (web)
    return (
      <View style={{ padding: 16 }}>
        <Text style={{ fontSize: 20, fontWeight: "700", marginBottom: 12 }}>Definir origem e destino (sem mapa)</Text>
        <Text style={{ fontWeight: "600" }}>Zona/Bairro de origem</Text>
        <TextInput
          value={origemLabel}
          onChangeText={setOrigemLabel}
          placeholder="Ex.: Cacém, Mem Martins..."
          style={{ borderWidth: 1, borderColor: "#ccc", borderRadius: 8, padding: 8, marginBottom: 12 }}
        />
        <Text style={{ fontWeight: "600" }}>Zona/Bairro de destino</Text>
        <TextInput
          value={destinoLabel}
          onChangeText={setDestinoLabel}
          placeholder="Ex.: Lisboa - Saldanha"
          style={{ borderWidth: 1, borderColor: "#ccc", borderRadius: 8, padding: 8, marginBottom: 16 }}
        />
        <Button title="Confirmar" onPress={confirm} />
        <View style={{ height: 12 }} />
        <Button title="Cancelar" onPress={onCancel} />
      </View>
    );
  }

  // Mobile com mapa
  return (
    <View style={{ flex: 1 }}>
      <View style={{ padding: 12 }}>
        <Text style={{ fontSize: 20, fontWeight: "700" }}>Seleciona origem e destino</Text>
        <Text style={{ opacity: 0.7, marginTop: 4 }}>Arrasta os marcadores. Toca no mapa para definir destino.</Text>
      </View>
      <MapView
        style={{ flex: 1 }}
        initialRegion={region}
        onPress={(e: any) => {
          const { latitude, longitude } = e.nativeEvent.coordinate;
          if (!origin) setOrigin({ lat: latitude, lng: longitude, label: "Origem" });
          else setDestination({ lat: latitude, lng: longitude, label: "Destino" });
        }}
      >
        {origin && (
          <Marker
            draggable
            coordinate={{ latitude: origin.lat, longitude: origin.lng }}
            title="Origem"
            pinColor="green"
            onDragEnd={(e: any) => {
              const { latitude, longitude } = e.nativeEvent.coordinate;
              setOrigin({ ...origin, lat: latitude, lng: longitude });
            }}
          />
        )}
        {destination && (
          <Marker
            draggable
            coordinate={{ latitude: destination.lat, longitude: destination.lng }}
            title="Destino"
            pinColor="red"
            onDragEnd={(e: any) => {
              const { latitude, longitude } = e.nativeEvent.coordinate;
              setDestination({ ...destination, lat: latitude, lng: longitude });
            }}
          />
        )}
      </MapView>
      <View style={{ padding: 12 }}>
        <Button title="Confirmar" onPress={confirm} />
        <View style={{ height: 8 }} />
        <Button title="Cancelar" onPress={onCancel} />
      </View>
    </View>
  );
}
