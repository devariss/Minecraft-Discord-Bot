package net.devariss.discordbotplugin;

import com.google.gson.Gson;

import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.AsyncPlayerChatEvent;
import org.bukkit.plugin.java.JavaPlugin;

import org.jetbrains.annotations.NotNull;

import java.io.*;

import java.net.Socket;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;

public final class DiscordBotPlugin extends JavaPlugin {
    private final StringBuilder PLAYER_MESSAGE_PAYLOAD = new StringBuilder();

    @Override
    public void onEnable() {
        registerEvents();
        connectToBotHost();
    }

    private void registerEvents() {
        final var EVENT_LISTENER = new Listener() {
            @EventHandler
            public void onPlayerMessage(@NotNull final AsyncPlayerChatEvent PLAYER_CHAT_EVENT) {
                synchronized (PLAYER_MESSAGE_PAYLOAD) {
                    PLAYER_MESSAGE_PAYLOAD.append(new Gson().toJson(new PlayerMessage(
                        PLAYER_CHAT_EVENT.getPlayer().getName(),
                        PLAYER_CHAT_EVENT.getMessage()
                    )));
                    PLAYER_MESSAGE_PAYLOAD.notifyAll();
                }
            }
        };
        getServer().getPluginManager().registerEvents(EVENT_LISTENER,this);
    }

    private void connectToBotHost() {
        Thread.startVirtualThread(() -> {
            while (isEnabled()) {
                try (
                    final var BOT_HOST = new Socket(getServer().getIp(), 7777);
                    final var HOST_SERVICE = Executors.newVirtualThreadPerTaskExecutor();
                    final var BOT_HOST_OUT = new PrintWriter(BOT_HOST.getOutputStream(),true);
                    final var BOT_HOST_IN = new BufferedReader(new InputStreamReader(BOT_HOST.getInputStream()))
                ) {
                    getLogger().info("Connected to bot host.");
                    HOST_SERVICE.submit(awaitPlayerMessages(BOT_HOST_OUT));
                    HOST_SERVICE.submit(awaitHostMessages(BOT_HOST_IN)).get();
                    HOST_SERVICE.shutdownNow();
                }
                catch (final IOException | InterruptedException | ExecutionException E) {
                    getLogger().warning("Bot host connection failed, attempting reconnect soon.\n%s".formatted(E));
                    try {
                        Thread.sleep(5000);
                    }
                    catch (InterruptedException ignored) {}
                }
            }
        });
    }

    private Runnable awaitPlayerMessages(PrintWriter botHostOut) {
        return () -> {
            while (true) {
                try {
                    synchronized (PLAYER_MESSAGE_PAYLOAD) {
                        PLAYER_MESSAGE_PAYLOAD.wait();
                        botHostOut.println("MESSAGE %s".formatted(PLAYER_MESSAGE_PAYLOAD));
                        if (!PLAYER_MESSAGE_PAYLOAD.isEmpty()) {
                            PLAYER_MESSAGE_PAYLOAD.delete(0, PLAYER_MESSAGE_PAYLOAD.length());
                            PLAYER_MESSAGE_PAYLOAD.trimToSize();
                        }
                    }
                }
                catch (final InterruptedException E) {
                    break;
                }
            }
        };
    }

    private Runnable awaitHostMessages(BufferedReader botHostIn) {
        return () -> {
            while (true) {
                try {
                    String botHostRequest = botHostIn.readLine();
                    int sepIndex = botHostRequest.indexOf(' ');
                    String jsonStr = botHostRequest.substring(sepIndex + 1);
                    String request = botHostRequest.substring(0, sepIndex);
                    switch (request) {
                        case "MESSAGE":
                            var message = new Gson().fromJson(jsonStr, DiscordMessage.class);
                            getServer().broadcastMessage("<%s: @%s> %s".formatted(message.channel, message.name, message.content));
                            break;
                        default:
                            getLogger().warning("Invalid request given (%s)".formatted(request));
                            break;
                    }
                }
                catch (final IOException E) {
                    getLogger().warning("Disconnected from bot host.\n%s".formatted(E));
                    break;
                }
            }
        };
    }

    private final class DiscordMessage {
        private final String name;
        private final String channel;
        private final String content;

        public DiscordMessage(String name, String channel, String content) {
            this.name = name;
            this.channel = channel;
            this.content = content;
        }
    }

    private final class PlayerMessage {
        private final String name;
        private final String content;

        public PlayerMessage(String name, String content) {
            this.name = name;
            this.content = content;
        }
    }
}