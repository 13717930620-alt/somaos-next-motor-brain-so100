# syntax=docker/dockerfile:1.7
# =============================================================================
# SomaOS Brain Next — closed-source container build
# (catalog entry: robonix.robot.somaos_next.motor_brain_so100)
# =============================================================================
# HOW THIS IMAGE IS BUILT
#   The image is built LOCALLY by the maintainer, on a machine that holds the
#   private sources. ./src is NOT part of this public repository and is never
#   pushed anywhere. Only compiled binary extensions enter the final image;
#   the source layer is dropped at the builder stage boundary.
#
# HOW TO RUN (community / reviewers)
#   Prebuilt image:  ghcr.io/13717930620-alt/somaos-motor-brain:latest
#   See install.md in this directory for pull/run instructions.
# =============================================================================

FROM python:3.12-slim AS builder
WORKDIR /build
# Private sources must be present locally at build time (never committed).
COPY src/ ./src/
# Compile the core to binary extensions. The produced .so files are the only
# thing carried over; no core source file survives into the runtime stage.
RUN pip install --no-cache-dir cython setuptools \
 && cythonize -i -3 src/core/*.py

FROM python:3.12-slim AS runtime
WORKDIR /opt/somaos
RUN useradd --system --uid 10001 somaos
# Compiled core only — no core sources in this layer.
COPY --from=builder /build/src/core/*.so ./core/
# Public, readable shell + demo packages (also present in this repository).
COPY service/ ./service/
COPY demos/ ./demos/
COPY docker/weight_client.py ./weight_client.py
COPY docker/entrypoint.sh /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint \
 && mkdir -p /var/lib/somaos/weights \
 && chown -R somaos:somaos /var/lib/somaos /opt/somaos
USER somaos
ENV SOMAOS_WEIGHTS_DIR=/var/lib/somaos/weights
EXPOSE 8766
ENTRYPOINT ["entrypoint"]
# Default: run the included, self-contained demo loop (no weights needed).
CMD ["--mode", "demo"]
