import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, TextInput, ActivityIndicator, ScrollView, LayoutAnimation, Platform, UIManager } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../context/ThemeContext';
import api from '../services/api';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

const sevColor = (sv) => {
  const map = { Low: '#3b82f6', Moderate: '#f59e0b', High: '#ef4444', 'Moderate to High': '#ef4444', 'Low to Moderate': '#f59e0b' };
  return map[sv] || '#6b7280';
};

function PestCard({ pest, theme }) {
  const [expanded, setExpanded] = useState(false);
  const color = sevColor(pest.severity_level);

  function toggle() {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpanded(!expanded);
  }

  return (
    <TouchableOpacity activeOpacity={0.7} onPress={toggle} style={[s.card, { backgroundColor: theme.card, borderColor: expanded ? color + '60' : theme.border }]}>
      {/* Header */}
      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
        <View style={[s.iconBox, { backgroundColor: color + '18' }]}>
          <Ionicons name="bug" size={22} color={color} />
        </View>
        <View style={{ flex: 1, marginLeft: 12 }}>
          <Text style={{ fontSize: 16, fontWeight: '700', color: theme.text }}>{pest.name}</Text>
          <Text style={{ fontSize: 12, color: theme.textSecondary, fontStyle: 'italic', marginTop: 2 }}>{pest.scientific_name}</Text>
        </View>
        <View style={[s.sevBadge, { backgroundColor: color + '20' }]}>
          <Text style={{ color, fontSize: 11, fontWeight: '700' }}>{pest.severity_level}</Text>
        </View>
      </View>

      {/* Description */}
      <Text style={{ color: theme.textSecondary, fontSize: 13, lineHeight: 19, marginTop: 10 }} numberOfLines={expanded ? undefined : 2}>{pest.description}</Text>

      {/* Expanded content */}
      {expanded && (
        <View style={{ marginTop: 14 }}>
          {/* Affected plants */}
          {pest.affected_plants?.length > 0 && (
            <View style={{ marginBottom: 14 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                <Ionicons name="leaf" size={14} color={theme.primary} />
                <Text style={{ color: theme.text, fontWeight: '700', fontSize: 13, marginLeft: 6 }}>Affected Plants</Text>
              </View>
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
                {pest.affected_plants.map((p, i) => (
                  <View key={i} style={{ backgroundColor: theme.primary + '12', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 }}>
                    <Text style={{ color: theme.primary, fontSize: 11, fontWeight: '600' }}>{p}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Symptoms */}
          {pest.symptoms?.length > 0 && (
            <Section title="Symptoms" icon="eye-outline" color="#f59e0b" items={pest.symptoms} theme={theme} />
          )}

          {/* Remedies */}
          {pest.remedies?.length > 0 && (
            <Section title="Remedies" icon="medkit-outline" color={theme.success} items={pest.remedies} theme={theme} />
          )}

          {/* Prevention */}
          {pest.precautions?.length > 0 && (
            <Section title="Prevention" icon="shield-checkmark-outline" color={theme.info} items={pest.precautions} theme={theme} />
          )}
        </View>
      )}

      {/* Expand indicator */}
      <View style={{ alignItems: 'center', marginTop: 8 }}>
        <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={16} color={theme.textSecondary} />
      </View>
    </TouchableOpacity>
  );
}

function Section({ title, icon, color, items, theme }) {
  return (
    <View style={{ marginBottom: 14 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
        <Ionicons name={icon} size={14} color={color} />
        <Text style={{ color: theme.text, fontWeight: '700', fontSize: 13, marginLeft: 6 }}>{title}</Text>
      </View>
      {items.map((item, i) => (
        <View key={i} style={{ flexDirection: 'row', alignItems: 'flex-start', marginBottom: 4, paddingLeft: 4 }}>
          <View style={{ width: 5, height: 5, borderRadius: 3, backgroundColor: color, marginTop: 6, marginRight: 8 }} />
          <Text style={{ color: theme.textSecondary, fontSize: 12, lineHeight: 18, flex: 1 }}>{item}</Text>
        </View>
      ))}
    </View>
  );
}

export default function PestLibraryScreen() {
  const { theme } = useTheme();
  const [pests, setPests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getPestLibrary();
        setPests(data);
      } catch (e) {
        console.log('Pest library error:', e);
      }
      setLoading(false);
    }
    load();
  }, []);

  const filtered = pests.filter(p =>
    !search || p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.scientific_name?.toLowerCase().includes(search.toLowerCase()) ||
    p.affected_plants?.some(ap => ap.toLowerCase().includes(search.toLowerCase()))
  );

  if (loading) return <View style={[s.center, { backgroundColor: theme.background }]}><ActivityIndicator size="large" color={theme.primary} /></View>;

  return (
    <View style={[s.container, { backgroundColor: theme.background }]}>
      {/* Header stats */}
      <View style={{ flexDirection: 'row', paddingHorizontal: 16, paddingTop: 12, paddingBottom: 8, gap: 8 }}>
        <View style={[s.statBox, { backgroundColor: theme.danger + '12', borderColor: theme.danger + '30' }]}>
          <Ionicons name="bug" size={18} color={theme.danger} />
          <Text style={{ fontSize: 20, fontWeight: '800', color: theme.danger, marginTop: 4 }}>{pests.filter(p => p.id < 100).length}</Text>
          <Text style={{ fontSize: 10, color: theme.textSecondary }}>Pests</Text>
        </View>
        <View style={[s.statBox, { backgroundColor: theme.warning + '12', borderColor: theme.warning + '30' }]}>
          <Ionicons name="flask" size={18} color={theme.warning} />
          <Text style={{ fontSize: 20, fontWeight: '800', color: theme.warning, marginTop: 4 }}>{pests.filter(p => p.id >= 100).length}</Text>
          <Text style={{ fontSize: 10, color: theme.textSecondary }}>Diseases</Text>
        </View>
        <View style={[s.statBox, { backgroundColor: theme.primary + '12', borderColor: theme.primary + '30' }]}>
          <Ionicons name="leaf" size={18} color={theme.primary} />
          <Text style={{ fontSize: 20, fontWeight: '800', color: theme.primary, marginTop: 4 }}>
            {[...new Set(pests.flatMap(p => p.affected_plants || []))].length}
          </Text>
          <Text style={{ fontSize: 10, color: theme.textSecondary }}>Plants</Text>
        </View>
      </View>

      {/* Search */}
      <View style={[s.searchRow, { borderColor: theme.border, backgroundColor: theme.card }]}>
        <Ionicons name="search" size={20} color={theme.textSecondary} />
        <TextInput style={[s.searchInput, { color: theme.text }]} placeholder="Search pests, diseases, or plants..." placeholderTextColor={theme.textSecondary} value={search} onChangeText={setSearch} />
        {search ? <TouchableOpacity onPress={() => setSearch('')}><Ionicons name="close-circle" size={18} color={theme.textSecondary} /></TouchableOpacity> : null}
      </View>

      {/* List */}
      <FlatList
        data={filtered}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => <PestCard pest={item} theme={theme} />}
        contentContainerStyle={{ padding: 16, paddingTop: 4 }}
        ListEmptyComponent={
          <View style={s.center}>
            <Ionicons name="search" size={48} color={theme.textSecondary} />
            <Text style={{ color: theme.textSecondary, marginTop: 12 }}>No pests match your search</Text>
          </View>
        }
      />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 60 },
  statBox: { flex: 1, padding: 12, borderRadius: 12, borderWidth: 1, alignItems: 'center' },
  searchRow: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 8, paddingHorizontal: 14, height: 44, borderRadius: 12, borderWidth: 1 },
  searchInput: { flex: 1, marginLeft: 10, fontSize: 14 },
  card: { borderRadius: 14, padding: 14, borderWidth: 1, marginBottom: 10 },
  iconBox: { width: 42, height: 42, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  sevBadge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 10 },
});
