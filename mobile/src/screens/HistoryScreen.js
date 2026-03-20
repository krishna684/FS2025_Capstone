import React, { useState, useEffect, useCallback, useRef } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, TextInput, ActivityIndicator, Animated, LayoutAnimation, Platform, UIManager } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import api from '../services/api';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

const FILTERS = ['All', 'Healthy', 'Mild', 'Moderate', 'High', 'Severe'];
const sevColor = (sv, t) => ({ Healthy: t.success, Mild: t.info, Moderate: t.warning, Severe: t.danger, High: t.danger }[sv] || t.textSecondary);
const sevIcon = (sv) => ({ Healthy: 'checkmark-circle', Mild: 'information-circle', Moderate: 'alert-circle', High: 'warning', Severe: 'skull' }[sv] || 'help-circle');

function ExpandableItem({ item, theme }) {
  const [expanded, setExpanded] = useState(false);
  const animHeight = useRef(new Animated.Value(0)).current;
  const animRotate = useRef(new Animated.Value(0)).current;

  const p = item.pest_identified || item.pest || 'Unknown';
  const pl = item.plant || item.crop_type || 'Plant';
  const d = (item.created_at || item.date || '').split('T')[0];
  const sv = item.severity || 'Unknown';
  const c = sevColor(sv, theme);
  const conf = item.confidence ? Math.round(item.confidence) : null;
  const status = item.status || '';
  const damage = item.damage_pattern || '';
  const hasFeedback = item.has_feedback;

  function toggle() {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    Animated.parallel([
      Animated.spring(animRotate, { toValue: expanded ? 0 : 1, friction: 8, useNativeDriver: true }),
    ]).start();
    setExpanded(!expanded);
  }

  const rotate = animRotate.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '180deg'] });

  return (
    <TouchableOpacity activeOpacity={0.7} onPress={toggle} style={[s.item, { backgroundColor: theme.card, borderColor: expanded ? c + '60' : theme.border, borderWidth: expanded ? 1.5 : 1 }]}>
      {/* Main row */}
      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
        <View style={[s.iconBox, { backgroundColor: c + '18' }]}>
          <Ionicons name={sevIcon(sv)} size={22} color={c} />
        </View>
        <View style={{ flex: 1, marginLeft: 12 }}>
          <Text style={[s.pest, { color: theme.text }]}>{p}</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 3 }}>
            <Ionicons name="leaf-outline" size={12} color={theme.textSecondary} />
            <Text style={{ color: theme.textSecondary, fontSize: 12, marginLeft: 4 }}>{pl}</Text>
            <Text style={{ color: theme.textSecondary, fontSize: 12, marginHorizontal: 6 }}>•</Text>
            <Ionicons name="calendar-outline" size={12} color={theme.textSecondary} />
            <Text style={{ color: theme.textSecondary, fontSize: 12, marginLeft: 4 }}>{d}</Text>
          </View>
        </View>
        <View style={{ alignItems: 'flex-end', marginRight: 8 }}>
          <View style={[s.sevBadge, { backgroundColor: c + '20' }]}>
            <Text style={{ color: c, fontSize: 11, fontWeight: '700' }}>{sv}</Text>
          </View>
          {conf != null && <Text style={{ color: theme.textSecondary, fontSize: 11, marginTop: 3, fontWeight: '600' }}>{conf}%</Text>}
        </View>
        <Animated.View style={{ transform: [{ rotate }] }}>
          <Ionicons name="chevron-down" size={18} color={theme.textSecondary} />
        </Animated.View>
      </View>

      {/* Expanded details */}
      {expanded && (
        <View style={{ marginTop: 14, borderTopWidth: 1, borderTopColor: theme.border, paddingTop: 14 }}>
          {/* Confidence bar */}
          {conf != null && (
            <View style={{ marginBottom: 12 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 }}>
                <Text style={{ color: theme.textSecondary, fontSize: 12, fontWeight: '600' }}>Confidence</Text>
                <Text style={{ color: theme.text, fontSize: 12, fontWeight: '700' }}>{conf}%</Text>
              </View>
              <View style={{ height: 6, backgroundColor: theme.border, borderRadius: 3 }}>
                <View style={{ height: 6, borderRadius: 3, backgroundColor: conf > 80 ? theme.success : theme.warning, width: conf + '%' }} />
              </View>
            </View>
          )}

          {/* Info rows */}
          {[
            { icon: 'pulse', label: 'Status', value: status, show: !!status },
            { icon: 'bug', label: 'Pest', value: p, show: p !== 'Unknown' },
            { icon: 'document-text', label: 'Description', value: damage, show: !!damage },
          ].filter(r => r.show).map((row, i) => (
            <View key={i} style={{ flexDirection: 'row', alignItems: 'flex-start', marginBottom: 8 }}>
              <Ionicons name={row.icon} size={14} color={c} style={{ marginTop: 2 }} />
              <View style={{ marginLeft: 8, flex: 1 }}>
                <Text style={{ color: theme.textSecondary, fontSize: 11, fontWeight: '600' }}>{row.label}</Text>
                <Text style={{ color: theme.text, fontSize: 13, marginTop: 1, lineHeight: 18 }}>{row.value}</Text>
              </View>
            </View>
          ))}

          {/* Feedback status */}
          <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 4, paddingTop: 8, borderTopWidth: 1, borderTopColor: theme.border }}>
            <Ionicons name={hasFeedback ? 'checkmark-circle' : 'chatbox-ellipses-outline'} size={14} color={hasFeedback ? theme.success : theme.textSecondary} />
            <Text style={{ color: hasFeedback ? theme.success : theme.textSecondary, fontSize: 11, marginLeft: 6, fontWeight: '600' }}>
              {hasFeedback ? 'Feedback submitted' : 'No feedback yet'}
            </Text>
          </View>
        </View>
      )}
    </TouchableOpacity>
  );
}

export default function HistoryScreen() {
  const { theme } = useTheme(); const { t } = useLanguage();
  const [history, setHistory] = useState([]); const [stats, setStats] = useState({});
  const [filter, setFilter] = useState('All'); const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true); const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const d = await api.getHistory();
      setHistory(d.history || []);
      setStats(d.stats || {});
    } catch (e) {
      setError('Unable to load history. Pull down to retry.');
      setHistory([]);
      setStats({ total_scans: 0, pests_found: 0, healthy: 0 });
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);
  const onRefresh = useCallback(async () => { setRefreshing(true); await load(); setRefreshing(false); }, [load]);

  const filtered = history.filter(i => {
    const p = i.pest_identified || i.pest || ''; const pl = i.plant || i.crop_type || ''; const sv = i.severity || '';
    return (filter === 'All' || sv === filter) && (!search || p.toLowerCase().includes(search.toLowerCase()) || pl.toLowerCase().includes(search.toLowerCase()));
  });

  if (loading) return <View style={[s.center, { backgroundColor: theme.background }]}><ActivityIndicator size="large" color={theme.primary} /></View>;

  return (
    <View style={[s.c, { backgroundColor: theme.background }]}>
      {/* Stats row */}
      <View style={s.statsRow}>
        {[
          { l: t('history.totalScans'), v: stats.total_scans || 0, c: theme.info, icon: 'analytics' },
          { l: t('history.pestsFound'), v: stats.pests_found || 0, c: theme.danger, icon: 'bug' },
          { l: 'Healthy', v: stats.healthy || 0, c: theme.success, icon: 'leaf' },
        ].map((st, i) => (
          <View key={i} style={[s.statBox, { backgroundColor: theme.card, borderColor: theme.border }]}>
            <Ionicons name={st.icon} size={18} color={st.c} />
            <Text style={[s.statVal, { color: st.c }]}>{st.v}</Text>
            <Text style={{ color: theme.textSecondary, fontSize: 10, marginTop: 2 }}>{st.l}</Text>
          </View>
        ))}
      </View>

      {/* Search bar */}
      <View style={[s.searchRow, { borderColor: theme.border, backgroundColor: theme.card }]}>
        <Ionicons name="search" size={20} color={theme.textSecondary} />
        <TextInput style={[s.searchInput, { color: theme.text }]} placeholder="Search pest or plant..." placeholderTextColor={theme.textSecondary} value={search} onChangeText={setSearch} />
        {search ? <TouchableOpacity onPress={() => setSearch('')}><Ionicons name="close-circle" size={18} color={theme.textSecondary} /></TouchableOpacity> : null}
      </View>

      {/* Filter chips — fixed height, no clipping */}
      <View style={{ paddingHorizontal: 12, paddingBottom: 8 }}>
        <FlatList
          data={FILTERS}
          horizontal
          showsHorizontalScrollIndicator={false}
          keyExtractor={(item) => item}
          contentContainerStyle={{ paddingHorizontal: 4 }}
          renderItem={({ item: f }) => (
            <TouchableOpacity
              style={[s.filterChip, {
                backgroundColor: filter === f ? theme.primary : theme.card,
                borderColor: filter === f ? theme.primary : theme.border,
              }]}
              onPress={() => setFilter(f)}
            >
              <Text style={{ color: filter === f ? '#fff' : theme.text, fontSize: 13, fontWeight: '600' }}>{f}</Text>
            </TouchableOpacity>
          )}
        />
      </View>

      {/* History list */}
      <FlatList
        data={filtered}
        keyExtractor={(_, i) => i.toString()}
        renderItem={({ item }) => <ExpandableItem item={item} theme={theme} />}
        contentContainerStyle={{ padding: 16, paddingTop: 4 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />}
        ListEmptyComponent={
          <View style={s.empty}>
            <Ionicons name={error ? "cloud-offline-outline" : "document-text-outline"} size={48} color={theme.textSecondary} />
            <Text style={{ color: theme.textSecondary, fontSize: 16, marginTop: 12, textAlign: 'center', paddingHorizontal: 30 }}>
              {error || (history.length === 0 ? 'No scans yet. Scan a plant to see your history!' : 'No results match your filter.')}
            </Text>
          </View>
        }
      />
    </View>
  );
}

const s = StyleSheet.create({
  c: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  statsRow: { flexDirection: 'row', padding: 16, paddingBottom: 10 },
  statBox: { flex: 1, padding: 12, borderRadius: 12, borderWidth: 1, alignItems: 'center', marginHorizontal: 4 },
  statVal: { fontSize: 22, fontWeight: '800', marginTop: 4 },
  searchRow: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 10, paddingHorizontal: 14, height: 44, borderRadius: 12, borderWidth: 1 },
  searchInput: { flex: 1, marginLeft: 10, fontSize: 14 },
  filterChip: { paddingHorizontal: 18, paddingVertical: 8, borderRadius: 20, borderWidth: 1, marginRight: 8 },
  item: { borderRadius: 14, padding: 14, borderWidth: 1, marginBottom: 10 },
  iconBox: { width: 42, height: 42, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  pest: { fontSize: 15, fontWeight: '700' },
  sevBadge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 10 },
  empty: { alignItems: 'center', paddingTop: 60 },
});
