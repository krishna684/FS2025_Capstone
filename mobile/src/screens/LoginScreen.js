import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, Alert, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';

export default function LoginScreen({ navigation }) {
  const { login } = useAuth();
  const { theme } = useTheme();
  const { t } = useLanguage();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    if (!email || !password) { Alert.alert(t('common.error'), 'Please enter email and password'); return; }
    setLoading(true);
    try { await login(email, password); } catch (e) { Alert.alert(t('common.error'), e.message); } finally { setLoading(false); }
  }

  return (
    <KeyboardAvoidingView style={[styles.container, { backgroundColor: theme.background }]} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.logoContainer}>
          <View style={[styles.logoCircle, { backgroundColor: theme.primary + '20' }]}>
            <Ionicons name="leaf" size={48} color={theme.primary} />
          </View>
          <Text style={[styles.brand, { color: theme.primary }]}>AGBOT</Text>
          <Text style={[styles.tagline, { color: theme.textSecondary }]}>From Data to Harvest</Text>
        </View>
        <View style={[styles.card, { backgroundColor: theme.card, borderColor: theme.border }]}>
          <Text style={[styles.title, { color: theme.text }]}>{t('login.title')}</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>{t('login.subtitle')}</Text>
          <View style={styles.inputGroup}>
            <Text style={[styles.label, { color: theme.textSecondary }]}>{t('login.email')}</Text>
            <View style={[styles.inputRow, { borderColor: theme.border, backgroundColor: theme.background }]}>
              <Ionicons name="mail-outline" size={20} color={theme.textSecondary} />
              <TextInput style={[styles.input, { color: theme.text }]} placeholder={t('login.email')} placeholderTextColor={theme.textSecondary} value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />
            </View>
          </View>
          <View style={styles.inputGroup}>
            <Text style={[styles.label, { color: theme.textSecondary }]}>{t('login.password')}</Text>
            <View style={[styles.inputRow, { borderColor: theme.border, backgroundColor: theme.background }]}>
              <Ionicons name="lock-closed-outline" size={20} color={theme.textSecondary} />
              <TextInput style={[styles.input, { color: theme.text }]} placeholder={t('login.password')} placeholderTextColor={theme.textSecondary} value={password} onChangeText={setPassword} secureTextEntry={!showPw} />
              <TouchableOpacity onPress={() => setShowPw(!showPw)}>
                <Ionicons name={showPw ? 'eye-off-outline' : 'eye-outline'} size={20} color={theme.textSecondary} />
              </TouchableOpacity>
            </View>
          </View>
          <TouchableOpacity style={[styles.button, { backgroundColor: theme.primary }]} onPress={handleLogin} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>{t('login.signin')}</Text>}
          </TouchableOpacity>
          <TouchableOpacity onPress={() => navigation.navigate('Register')} style={styles.linkRow}>
            <Text style={{ color: theme.textSecondary, fontSize: 14 }}>{t('login.noaccount')} </Text>
            <Text style={{ color: theme.primary, fontSize: 14, fontWeight: '700' }}>{t('login.signup')}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 }, scroll: { flexGrow: 1, justifyContent: 'center', padding: 20 },
  logoContainer: { alignItems: 'center', marginBottom: 32 },
  logoCircle: { width: 88, height: 88, borderRadius: 44, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  brand: { fontSize: 32, fontWeight: '800', letterSpacing: 2 }, tagline: { fontSize: 14, marginTop: 4 },
  card: { borderRadius: 16, padding: 24, borderWidth: 1 },
  title: { fontSize: 24, fontWeight: '700', textAlign: 'center' },
  subtitle: { fontSize: 14, textAlign: 'center', marginTop: 4, marginBottom: 24 },
  inputGroup: { marginBottom: 16 }, label: { fontSize: 13, fontWeight: '600', marginBottom: 6 },
  inputRow: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: 12, paddingHorizontal: 14, height: 48 },
  input: { flex: 1, marginLeft: 10, fontSize: 15 },
  button: { height: 50, borderRadius: 12, alignItems: 'center', justifyContent: 'center', marginTop: 8 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  linkRow: { flexDirection: 'row', justifyContent: 'center', marginTop: 20 },
});
