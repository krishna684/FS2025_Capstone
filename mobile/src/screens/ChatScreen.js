import React, { useState, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../context/ThemeContext';
import api from '../services/api';

const SUGGESTIONS = [
  'How do I get rid of aphids?',
  'What are symptoms of spider mites?',
  'How to prevent whiteflies?',
  'Tell me about caterpillars',
  'How to treat powdery mildew?',
];

export default function ChatScreen() {
  const { theme } = useTheme();
  const [messages, setMessages] = useState([
    { id: '0', text: "Hi! I'm AGBOT, your pest detection assistant. Ask me about any plant pest — symptoms, remedies, or prevention tips!", sender: 'bot' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const flatListRef = useRef(null);

  async function send(text) {
    const msg = (text || input).trim();
    if (!msg || loading) return;

    const userMsg = { id: Date.now().toString(), text: msg, sender: 'user' };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const data = await api.chat(msg);
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), text: data.reply, sender: 'bot' }]);
    } catch (e) {
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), text: 'Sorry, I could not process that. Please try again.', sender: 'bot' }]);
    }
    setLoading(false);
    setTimeout(() => flatListRef.current?.scrollToEnd(), 100);
  }

  const renderMessage = ({ item }) => {
    const isBot = item.sender === 'bot';
    return (
      <View style={[s.msgRow, { justifyContent: isBot ? 'flex-start' : 'flex-end' }]}>
        {isBot && (
          <View style={[s.avatar, { backgroundColor: theme.primary + '20' }]}>
            <Ionicons name="leaf" size={16} color={theme.primary} />
          </View>
        )}
        <View style={[s.bubble, {
          backgroundColor: isBot ? theme.card : theme.primary,
          borderColor: isBot ? theme.border : theme.primary,
          borderBottomLeftRadius: isBot ? 4 : 18,
          borderBottomRightRadius: isBot ? 18 : 4,
          maxWidth: '78%',
        }]}>
          <Text style={[s.msgText, { color: isBot ? theme.text : '#fff' }]}>{item.text}</Text>
        </View>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView style={[s.container, { backgroundColor: theme.background }]} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={90}>
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={item => item.id}
        renderItem={renderMessage}
        contentContainerStyle={{ padding: 16, paddingBottom: 8 }}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
        ListHeaderComponent={
          messages.length <= 1 ? (
            <View style={{ marginBottom: 16 }}>
              <Text style={{ color: theme.textSecondary, fontSize: 13, marginBottom: 10 }}>Try asking:</Text>
              {SUGGESTIONS.map((q, i) => (
                <TouchableOpacity key={i} style={[s.suggestion, { backgroundColor: theme.card, borderColor: theme.border }]} onPress={() => send(q)}>
                  <Ionicons name="chatbubble-outline" size={14} color={theme.primary} />
                  <Text style={{ color: theme.text, fontSize: 13, marginLeft: 8, flex: 1 }}>{q}</Text>
                  <Ionicons name="arrow-forward" size={14} color={theme.textSecondary} />
                </TouchableOpacity>
              ))}
            </View>
          ) : null
        }
      />

      {loading && (
        <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingBottom: 8 }}>
          <View style={[s.avatar, { backgroundColor: theme.primary + '20', width: 28, height: 28 }]}>
            <Ionicons name="leaf" size={12} color={theme.primary} />
          </View>
          <View style={[s.typingDots, { backgroundColor: theme.card, borderColor: theme.border }]}>
            <ActivityIndicator size="small" color={theme.primary} />
            <Text style={{ color: theme.textSecondary, fontSize: 12, marginLeft: 8 }}>Thinking...</Text>
          </View>
        </View>
      )}

      <View style={[s.inputRow, { backgroundColor: theme.card, borderColor: theme.border }]}>
        <TextInput
          style={[s.input, { color: theme.text }]}
          placeholder="Ask about a pest..."
          placeholderTextColor={theme.textSecondary}
          value={input}
          onChangeText={setInput}
          onSubmitEditing={() => send()}
          returnKeyType="send"
          editable={!loading}
        />
        <TouchableOpacity style={[s.sendBtn, { backgroundColor: input.trim() ? theme.primary : theme.border }]} onPress={() => send()} disabled={!input.trim() || loading}>
          <Ionicons name="send" size={18} color="#fff" />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1 },
  msgRow: { flexDirection: 'row', alignItems: 'flex-end', marginBottom: 10 },
  avatar: { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center', marginRight: 8 },
  bubble: { padding: 12, borderRadius: 18, borderWidth: 1 },
  msgText: { fontSize: 14, lineHeight: 20 },
  suggestion: { flexDirection: 'row', alignItems: 'center', padding: 12, borderRadius: 12, borderWidth: 1, marginBottom: 6 },
  typingDots: { flexDirection: 'row', alignItems: 'center', padding: 10, borderRadius: 18, borderWidth: 1, marginLeft: 8 },
  inputRow: { flexDirection: 'row', alignItems: 'center', padding: 8, borderTopWidth: 1, paddingBottom: 28 },
  input: { flex: 1, fontSize: 15, paddingHorizontal: 14, height: 42 },
  sendBtn: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
});
