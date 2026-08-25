FROM eclipse-temurin:17-jdk-jammy AS builder

ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV PATH=${PATH}:${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/platform-tools

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl unzip git && rm -rf /var/lib/apt/lists/*

RUN mkdir -p ${ANDROID_SDK_ROOT}/cmdline-tools && \
    curl -o cmdline-tools.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip && \
    unzip -q cmdline-tools.zip -d ${ANDROID_SDK_ROOT}/cmdline-tools && \
    mv ${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools ${ANDROID_SDK_ROOT}/cmdline-tools/latest && \
    rm cmdline-tools.zip

RUN yes | sdkmanager --licenses > /dev/null && \
    sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

WORKDIR /app
COPY . .

ARG WIFI_ADDRESS=10.0.2.2
ARG NESTO_API_KEY=
ENV WIFI_ADDRESS=${WIFI_ADDRESS}
ENV NESTO_API_KEY=${NESTO_API_KEY}

RUN chmod +x ./gradlew
RUN sed -i 's/\r$//' gradlew && chmod +x gradlew
RUN ./gradlew assembleDebug --no-daemon