(() => {
  "use strict";

  const SOURCE_WIDTH = 1672;
  const SOURCE_HEIGHT = 941;
  const stage = document.querySelector("[data-ecml-hero-media]");
  const image = stage?.querySelector(".ecml-hero-base");
  const canvas = stage?.querySelector("[data-ecml-overlay]");
  const context = canvas?.getContext("2d", { alpha: true, desynchronized: true });

  if (!stage || !image || !canvas || !context) return;

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const controls = [...document.querySelectorAll("[data-ecml-layer]")];
  const explore = document.querySelector(".home-explore");

  const masks = {
    desalination: [
      [[851, 218], [993, 226], [993, 391], [851, 379]],
      [[1022, 217], [1439, 198], [1439, 378], [1022, 397]],
    ],
    intelligent: [
      [[851, 428], [993, 434], [993, 585], [851, 568]],
      [[1022, 431], [1439, 415], [1439, 576], [1022, 595]],
    ],
    sustainable: [
      [[851, 615], [993, 626], [993, 797], [851, 772]],
      [[1022, 626], [1439, 606], [1439, 747], [1022, 797]],
    ],
  };

  const labelPanels = [
    {
      layer: "desalination",
      polygon: [[676, 208], [844, 214], [844, 389], [676, 382]],
      lines: ["Modeling", "& Design"],
      baseline: [286, 315],
      fontSize: 18.5,
      accent: [70, 224, 255],
    },
    {
      layer: "intelligent",
      polygon: [[676, 414], [844, 420], [844, 582], [676, 574]],
      lines: ["AI", "Systems"],
      baseline: [490, 520],
      fontSize: 20,
      accent: [154, 116, 255],
    },
    {
      layer: "sustainable",
      polygon: [[676, 609], [844, 616], [844, 771], [676, 760]],
      lines: ["Sustainability", "& Environment"],
      baseline: [681, 710],
      fontSize: 19,
      accent: [78, 236, 190],
    },
  ];

  const topPaths = [
    [[868, 258], [955, 244], [1038, 267], [1118, 292], [1238, 321], [1322, 286], [1418, 303]],
    [[865, 278], [960, 260], [1030, 285], [1116, 301], [1210, 322], [1310, 295], [1420, 322]],
    [[861, 296], [945, 281], [1032, 301], [1116, 310], [1210, 319], [1300, 315], [1418, 337]],
    [[861, 316], [958, 296], [1035, 315], [1117, 319], [1210, 322], [1295, 338], [1412, 350]],
    [[868, 337], [960, 317], [1039, 327], [1123, 326], [1210, 326], [1290, 354], [1404, 359]],
    [[870, 350], [958, 332], [1035, 341], [1120, 337], [1212, 333], [1294, 360], [1400, 368]],
  ];

  const topRibbonPaths = [
    [[1034, 278], [1090, 276], [1172, 287], [1225, 308], [1280, 329], [1341, 291], [1418, 300]],
    [[1034, 324], [1094, 318], [1171, 321], [1228, 329], [1291, 337], [1348, 356], [1412, 350]],
  ];

  const networkNodes = [
    [891, 498], [930, 487], [976, 470], [989, 520], [1036, 503], [1066, 534],
    [1098, 462], [1112, 511], [1167, 498], [1172, 579], [1205, 455], [1205, 533],
    [1244, 558], [1264, 497], [1295, 536], [1316, 476], [1330, 551], [1351, 522],
    [1394, 512], [939, 557], [871, 541],
  ];

  const networkEdges = [
    [0, 1], [1, 2], [1, 3], [2, 6], [3, 4], [3, 19], [4, 7], [5, 7],
    [6, 8], [6, 10], [7, 8], [7, 11], [8, 10], [8, 13], [9, 12], [10, 13],
    [11, 12], [11, 14], [12, 16], [13, 15], [13, 17], [14, 17], [15, 18], [16, 17],
    [17, 18], [19, 5], [20, 0], [20, 19],
  ];

  const brainPaths = [
    [[866, 526], [912, 503], [946, 544], [993, 513], [1040, 482], [1078, 551], [1121, 511], [1165, 471], [1208, 545], [1250, 504], [1292, 468], [1341, 530], [1407, 493]],
    [[866, 545], [913, 520], [952, 562], [996, 532], [1043, 503], [1081, 570], [1126, 530], [1169, 491], [1211, 564], [1253, 523], [1295, 489], [1344, 549], [1407, 513]],
    [[870, 560], [916, 538], [956, 576], [1000, 548], [1047, 521], [1085, 582], [1130, 547], [1173, 509], [1215, 578], [1257, 539], [1299, 507], [1348, 565], [1404, 531]],
  ];

  let randomState = 0x5ec01a;
  const random = () => {
    randomState ^= randomState << 13;
    randomState ^= randomState >>> 17;
    randomState ^= randomState << 5;
    return (randomState >>> 0) / 4294967296;
  };

  const topParticles = Array.from({ length: 40 }, (_, index) => ({
    path: index % topPaths.length,
    phase: random(),
    speed: 0.04 + random() * 0.045,
    size: 0.85 + random() * 1.45,
  }));
  const topBubbles = Array.from({ length: 14 }, (_, index) => ({
    path: index % topRibbonPaths.length,
    phase: random(),
    speed: 0.027 + random() * 0.024,
    size: 1.2 + random() * 2.25,
    drift: random() * Math.PI * 2,
  }));
  const networkPulses = Array.from({ length: 14 }, (_, index) => ({
    edge: (index * 5 + 2) % networkEdges.length,
    phase: random(),
    speed: 0.055 + random() * 0.045,
    size: 1.1 + random() * 1.5,
  }));
  const loopParticles = Array.from({ length: 24 }, (_, index) => ({
    phase: (index / 24) * Math.PI * 2 + random() * 0.14,
    speed: 0.21 + random() * 0.13,
    size: 1.05 + random() * 1.45,
  }));

  let mapping = { sx: 1, sy: 1, dx: 0, dy: 0, width: 1, height: 1, dpr: 1 };
  let activeLayer = "default";
  let animationFrame = 0;
  let lastFrameTime = 0;
  let pageVisible = !document.hidden;
  let stageVisible = true;
  let mobile = false;

  const percentage = (value, fallback) => {
    if (!value) return fallback;
    if (value === "left" || value === "top") return 0;
    if (value === "center") return 0.5;
    if (value === "right" || value === "bottom") return 1;
    if (value.endsWith("%")) return Number.parseFloat(value) / 100;
    return fallback;
  };

  const updateMapping = () => {
    const rect = stage.getBoundingClientRect();
    if (!rect.width || !rect.height) return;

    const style = getComputedStyle(image);
    const position = style.objectPosition.trim().split(/\s+/);
    const positionX = percentage(position[0], 0.5);
    const positionY = percentage(position[1], 0.5);
    const fit = style.objectFit;
    let sx = rect.width / SOURCE_WIDTH;
    let sy = rect.height / SOURCE_HEIGHT;

    if (fit === "cover" || fit === "contain") {
      const scale = fit === "cover" ? Math.max(sx, sy) : Math.min(sx, sy);
      sx = scale;
      sy = scale;
    } else if (fit === "none") {
      sx = 1;
      sy = 1;
    }

    const renderedWidth = SOURCE_WIDTH * sx;
    const renderedHeight = SOURCE_HEIGHT * sy;
    const dx = (rect.width - renderedWidth) * positionX;
    const dy = (rect.height - renderedHeight) * positionY;
    mobile = window.innerWidth < 768 || rect.width < 600;
    const dpr = Math.min(window.devicePixelRatio || 1, mobile ? 1.5 : 2);

    mapping = { sx, sy, dx, dy, width: rect.width, height: rect.height, dpr };
    const pixelWidth = Math.max(1, Math.round(rect.width * dpr));
    const pixelHeight = Math.max(1, Math.round(rect.height * dpr));
    if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
      canvas.width = pixelWidth;
      canvas.height = pixelHeight;
    }

    stage.querySelectorAll("[data-source-box]").forEach((control) => {
      const [x, y, width, height] = control.dataset.sourceBox.split(",").map(Number);
      control.style.left = `${dx + x * sx}px`;
      control.style.top = `${dy + y * sy}px`;
      control.style.width = `${width * sx}px`;
      control.style.height = `${height * sy}px`;
    });

    draw(performance.now() * 0.001, true);
  };

  const beginSourceTransform = () => {
    const { dpr, sx, sy, dx, dy } = mapping;
    context.setTransform(dpr * sx, 0, 0, dpr * sy, dpr * dx, dpr * dy);
  };

  const clear = () => {
    context.setTransform(1, 0, 0, 1, 0, 0);
    context.clearRect(0, 0, canvas.width, canvas.height);
    beginSourceTransform();
  };

  const clipLayer = (layer) => {
    context.beginPath();
    masks[layer].forEach((polygon) => {
      polygon.forEach(([x, y], index) => {
        if (index === 0) context.moveTo(x, y);
        else context.lineTo(x, y);
      });
      context.closePath();
    });
    context.clip();
  };

  const intensityFor = (layer) => {
    if (activeLayer === "default") return 0.82;
    return activeLayer === layer ? 1.34 : 0.24;
  };

  const cubicPoint = (p0, p1, p2, p3, t) => {
    const mt = 1 - t;
    const mt2 = mt * mt;
    const t2 = t * t;
    return [
      p0[0] * mt2 * mt + 3 * p1[0] * mt2 * t + 3 * p2[0] * mt * t2 + p3[0] * t2 * t,
      p0[1] * mt2 * mt + 3 * p1[1] * mt2 * t + 3 * p2[1] * mt * t2 + p3[1] * t2 * t,
    ];
  };

  const pointOnDoubleCubic = (path, progress) => {
    if (progress < 0.5) return cubicPoint(path[0], path[1], path[2], path[3], progress * 2);
    return cubicPoint(path[3], path[4], path[5], path[6], (progress - 0.5) * 2);
  };

  const traceDoubleCubic = (path) => {
    context.beginPath();
    context.moveTo(path[0][0], path[0][1]);
    context.bezierCurveTo(path[1][0], path[1][1], path[2][0], path[2][1], path[3][0], path[3][1]);
    context.bezierCurveTo(path[4][0], path[4][1], path[5][0], path[5][1], path[6][0], path[6][1]);
  };

  const tracePolygon = (polygon) => {
    context.beginPath();
    polygon.forEach(([x, y], index) => {
      if (index === 0) context.moveTo(x, y);
      else context.lineTo(x, y);
    });
    context.closePath();
  };

  const drawInactiveWash = () => {
    if (activeLayer === "default") return;
    Object.keys(masks).forEach((layer) => {
      if (layer === activeLayer) return;
      context.save();
      clipLayer(layer);
      context.globalCompositeOperation = "source-over";
      context.fillStyle = "rgba(1, 7, 20, 0.115)";
      context.fillRect(820, 175, 650, 650);
      context.restore();
    });
  };

  const drawTop = (time, still) => {
    const intensity = intensityFor("desalination");
    const pathCount = mobile ? 4 : 6;
    const particleCount = mobile ? 15 : 38;
    context.save();
    clipLayer("desalination");
    context.globalCompositeOperation = "screen";
    context.lineCap = "round";
    context.lineJoin = "round";

    const ribbonCount = mobile ? 1 : topRibbonPaths.length;
    for (let index = 0; index < ribbonCount; index += 1) {
      const path = topRibbonPaths[index];
      const ribbonGradient = context.createLinearGradient(1025, 0, 1425, 0);
      ribbonGradient.addColorStop(0, `rgba(56, 208, 245, ${0.025 * intensity})`);
      ribbonGradient.addColorStop(0.48, `rgba(126, 239, 255, ${0.11 * intensity})`);
      ribbonGradient.addColorStop(1, `rgba(63, 197, 255, ${0.035 * intensity})`);

      context.save();
      context.filter = "blur(4.5px)";
      context.strokeStyle = ribbonGradient;
      context.lineWidth = 8.5;
      context.setLineDash([88, 126]);
      context.lineDashOffset = still ? -index * 64 : -time * 48 - index * 64;
      traceDoubleCubic(path);
      context.stroke();
      context.restore();

      context.strokeStyle = `rgba(149, 243, 255, ${0.095 * intensity})`;
      context.lineWidth = 1.35;
      context.setLineDash([46, 118]);
      context.lineDashOffset = still ? -index * 51 : -time * 56 - index * 51;
      traceDoubleCubic(path);
      context.stroke();
    }

    for (let index = 0; index < pathCount; index += 1) {
      const path = topPaths[index];
      context.save();
      context.filter = "blur(2.2px)";
      context.strokeStyle = `rgba(61, 213, 255, ${0.07 * intensity})`;
      context.lineWidth = 5.2;
      context.setLineDash([48, 118]);
      context.lineDashOffset = still ? -index * 22 : -time * 34 - index * 22;
      traceDoubleCubic(path);
      context.stroke();
      context.restore();

      context.strokeStyle = `rgba(105, 230, 255, ${0.15 * intensity})`;
      context.lineWidth = 1.15;
      context.setLineDash([30, 82]);
      context.lineDashOffset = still ? -index * 18 : -time * 42 - index * 18;
      traceDoubleCubic(path);
      context.stroke();
    }

    context.setLineDash([]);
    context.shadowColor = "rgba(88, 226, 255, .72)";
    context.shadowBlur = 6.5;
    for (let index = 0; index < particleCount; index += 1) {
      const particle = topParticles[index];
      const progress = still ? particle.phase : (particle.phase + time * particle.speed) % 1;
      const [x, y] = pointOnDoubleCubic(topPaths[particle.path], progress);
      const pulse = 0.55 + Math.sin(progress * Math.PI) * 0.45;
      if (!mobile && progress > 0.025) {
        const [tailX, tailY] = pointOnDoubleCubic(topPaths[particle.path], progress - 0.025);
        context.strokeStyle = `rgba(116, 232, 255, ${0.11 * intensity * pulse})`;
        context.lineWidth = Math.max(0.55, particle.size * 0.72);
        context.beginPath();
        context.moveTo(tailX, tailY);
        context.lineTo(x, y);
        context.stroke();
      }
      context.fillStyle = `rgba(145, 240, 255, ${0.23 * intensity * pulse})`;
      context.beginPath();
      context.arc(x, y, particle.size, 0, Math.PI * 2);
      context.fill();
    }

    const bubbleCount = mobile ? 5 : 12;
    context.shadowBlur = 4;
    for (let index = 0; index < bubbleCount; index += 1) {
      const bubble = topBubbles[index];
      const progress = still ? bubble.phase : (bubble.phase + time * bubble.speed) % 1;
      const [baseX, baseY] = pointOnDoubleCubic(topRibbonPaths[bubble.path], progress);
      const drift = Math.sin(time * 0.8 + bubble.drift + progress * 8) * 2.2;
      const fade = Math.sin(progress * Math.PI);
      context.strokeStyle = `rgba(181, 245, 255, ${0.15 * intensity * fade})`;
      context.lineWidth = 0.65;
      context.beginPath();
      context.arc(baseX, baseY + drift, bubble.size, 0, Math.PI * 2);
      context.stroke();
    }
    context.restore();
  };

  const drawMiddle = (time, still) => {
    const intensity = intensityFor("intelligent");
    const traceCount = mobile ? 2 : 3;
    const pulseCount = mobile ? 6 : 13;
    const nodeCount = mobile ? 5 : 10;
    context.save();
    clipLayer("intelligent");
    context.globalCompositeOperation = "screen";
    context.lineCap = "round";

    for (let index = 0; index < traceCount; index += 1) {
      const path = brainPaths[index];
      context.save();
      context.filter = "blur(2px)";
      context.strokeStyle = `rgba(122, 105, 255, ${0.075 * intensity})`;
      context.lineWidth = 4.6;
      context.setLineDash([40, 136]);
      context.lineDashOffset = still ? -index * 31 : -time * (23 + index * 3) - index * 31;
      traceDoubleCubic(path);
      context.stroke();
      context.restore();

      context.strokeStyle = `rgba(181, 166, 255, ${0.135 * intensity})`;
      context.lineWidth = 1;
      context.setLineDash([27, 96]);
      context.lineDashOffset = still ? -index * 24 : -time * (29 + index * 2) - index * 24;
      traceDoubleCubic(path);
      context.stroke();
    }

    context.setLineDash([]);
    context.shadowColor = "rgba(150, 125, 255, .88)";
    context.shadowBlur = 8;
    for (let index = 0; index < pulseCount; index += 1) {
      const pulse = networkPulses[index];
      const [fromIndex, toIndex] = networkEdges[pulse.edge];
      const from = networkNodes[fromIndex];
      const to = networkNodes[toIndex];
      const progress = still ? pulse.phase : (pulse.phase + time * pulse.speed) % 1;
      const x = from[0] + (to[0] - from[0]) * progress;
      const y = from[1] + (to[1] - from[1]) * progress;
      context.fillStyle = `rgba(205, 194, 255, ${0.37 * intensity})`;
      context.beginPath();
      context.arc(x, y, pulse.size, 0, Math.PI * 2);
      context.fill();
    }

    for (let index = 0; index < nodeCount; index += 1) {
      const nodeIndex = (index * 2 + 1) % networkNodes.length;
      const [x, y] = networkNodes[nodeIndex];
      const wave = still ? 0.36 : Math.pow(Math.max(0, Math.sin(time * (0.75 + index * 0.027) + index * 1.73)), 6);
      const radius = 2.4 + wave * 4.8;
      context.fillStyle = `rgba(227, 220, 255, ${(0.07 + wave * 0.29) * intensity})`;
      context.beginPath();
      context.arc(x, y, radius, 0, Math.PI * 2);
      context.fill();
    }

    if (!still) {
      const sparkLimit = mobile ? 1 : 2;
      for (let index = 0; index < sparkLimit; index += 1) {
        const spark = Math.sin(time * (0.67 + index * 0.11) + index * 4.7);
        if (spark < 0.968) continue;
        const [x, y] = networkNodes[(index * 9 + 6) % networkNodes.length];
        const alpha = ((spark - 0.968) / 0.032) * 0.6 * intensity;
        context.strokeStyle = `rgba(245, 242, 255, ${alpha})`;
        context.lineWidth = 1;
        context.beginPath();
        context.moveTo(x - 4.5, y);
        context.lineTo(x + 4.5, y);
        context.moveTo(x, y - 4.5);
        context.lineTo(x, y + 4.5);
        context.stroke();
      }
    }
    context.restore();
  };

  const drawBottom = (time, still) => {
    const intensity = intensityFor("sustainable");
    const particleCount = mobile ? 10 : 23;
    const centerX = 1139;
    const centerY = 711;
    context.save();
    clipLayer("sustainable");
    context.globalCompositeOperation = "screen";
    context.lineCap = "round";

    for (let index = 0; index < 3; index += 1) {
      const phase = still ? 0.42 : Math.pow((Math.sin(time * 1.08 - index * 2.08) + 1) * 0.5, 5);
      context.save();
      context.filter = "blur(3px)";
      context.strokeStyle = `rgba(91, 239, 211, ${(0.025 + phase * 0.12) * intensity})`;
      context.lineWidth = 8;
      context.beginPath();
      context.ellipse(centerX, centerY, 249, 58, 0, index * 2.08 + 0.18, index * 2.08 + 1.56);
      context.stroke();
      context.restore();
    }

    context.shadowColor = "rgba(91, 237, 211, .8)";
    context.shadowBlur = 7.5;
    for (let index = 0; index < particleCount; index += 1) {
      const particle = loopParticles[index];
      const angle = still ? particle.phase : particle.phase + time * particle.speed;
      const x = centerX + Math.cos(angle) * 249;
      const y = centerY + Math.sin(angle) * 58;
      const depth = 0.65 + 0.35 * ((Math.sin(angle) + 1) * 0.5);
      context.fillStyle = `rgba(151, 255, 232, ${0.31 * intensity * depth})`;
      context.beginPath();
      context.arc(x, y, particle.size * depth * (mobile ? 1.2 : 1), 0, Math.PI * 2);
      context.fill();
    }

    const rippleCount = mobile ? 1 : 3;
    context.shadowBlur = 0;
    for (let index = 0; index < rippleCount; index += 1) {
      const progress = still ? (index + 1) / (rippleCount + 1) : (time * 0.16 + index / rippleCount) % 1;
      context.strokeStyle = `rgba(111, 237, 222, ${(1 - progress) * 0.1 * intensity})`;
      context.lineWidth = 1.1;
      context.beginPath();
      context.ellipse(1130, 712, 74 + progress * 72, 13 + progress * 14, 0, 0, Math.PI * 2);
      context.stroke();
    }

    const iconPulse = still ? 0.5 : (Math.sin(time * 0.72) + 1) * 0.5;
    context.save();
    context.translate(1326, 655);
    context.rotate(-0.16);
    context.scale(1.28, 1.28);
    context.shadowColor = "rgba(83, 239, 187, .72)";
    context.shadowBlur = 9;
    context.fillStyle = `rgba(112, 242, 194, ${(0.17 + iconPulse * 0.075) * intensity})`;
    context.strokeStyle = `rgba(164, 255, 221, ${(0.38 + iconPulse * 0.1) * intensity})`;
    context.lineWidth = 1.05;
    context.beginPath();
    context.moveTo(0, 13);
    context.bezierCurveTo(-18, 8, -18, -8, 0, -11);
    context.bezierCurveTo(9, -3, 8, 8, 0, 13);
    context.closePath();
    context.fill();
    context.stroke();
    context.beginPath();
    context.moveTo(-1, 11);
    context.bezierCurveTo(-1, 4, -4, -2, -10, -6);
    context.stroke();
    context.beginPath();
    context.moveTo(2, 12);
    context.bezierCurveTo(19, 9, 21, -5, 8, -12);
    context.bezierCurveTo(0, -3, 1, 7, 2, 12);
    context.closePath();
    context.fill();
    context.stroke();
    context.restore();

    context.save();
    context.translate(1363, 730);
    context.globalCompositeOperation = "source-over";
    context.shadowColor = "rgba(238, 197, 97, .42)";
    context.shadowBlur = 7;
    context.fillStyle = `rgba(5, 22, 29, ${0.58 + intensity * 0.08})`;
    context.beginPath();
    context.arc(0, 0, 15, 0, Math.PI * 2);
    context.fill();
    context.globalCompositeOperation = "screen";
    context.strokeStyle = `rgba(248, 214, 126, ${0.5 * intensity})`;
    context.lineWidth = 1.3;
    context.beginPath();
    context.arc(0, 0, 13.8, 0, Math.PI * 2);
    context.stroke();
    context.fillStyle = `rgba(255, 232, 164, ${0.72 * intensity})`;
    context.font = '700 18px "Inter", "Segoe UI", sans-serif';
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText("$", 0, 0.5);
    context.restore();
    context.restore();
  };

  const drawReplacementLabels = () => {
    labelPanels.forEach(({ layer, polygon, lines, baseline, accent, fontSize }) => {
      const selected = activeLayer === layer;
      const muted = activeLayer !== "default" && !selected;
      const labelStrength = selected ? 1.12 : muted ? 0.74 : 1;
      const [red, green, blue] = accent;

      context.save();
      context.globalCompositeOperation = "source-over";
      tracePolygon(polygon);
      const panelGradient = context.createLinearGradient(676, 0, 844, 0);
      panelGradient.addColorStop(0, "rgb(2, 10, 24)");
      panelGradient.addColorStop(0.64, "rgb(4, 15, 32)");
      panelGradient.addColorStop(1, "rgb(5, 19, 38)");
      context.fillStyle = panelGradient;
      context.fill();

      context.globalCompositeOperation = "screen";
      context.strokeStyle = `rgba(${red}, ${green}, ${blue}, ${0.085 * labelStrength})`;
      context.lineWidth = 0.75;
      tracePolygon(polygon);
      context.stroke();

      context.globalCompositeOperation = "source-over";
      context.fillStyle = `rgba(235, 243, 250, ${0.94 * labelStrength})`;
      context.font = `600 ${fontSize}px "Inter", "Segoe UI", sans-serif`;
      context.textAlign = "left";
      context.textBaseline = "alphabetic";
      if ("letterSpacing" in context) context.letterSpacing = "0.2px";
      lines.forEach((line, index) => context.fillText(line, 701, baseline[index]));

      context.globalCompositeOperation = "screen";
      context.shadowColor = `rgba(${red}, ${green}, ${blue}, .5)`;
      context.shadowBlur = selected ? 6 : 3;
      context.strokeStyle = `rgba(${red}, ${green}, ${blue}, ${0.64 * labelStrength})`;
      context.lineWidth = 1.45;
      context.beginPath();
      const finalBaseline = baseline[baseline.length - 1];
      context.moveTo(702, finalBaseline + 20);
      context.lineTo(selected ? 738 : 728, finalBaseline + 22);
      context.stroke();
      context.restore();
    });
  };

  function draw(time, still = false) {
    clear();
    drawInactiveWash();
    drawTop(time, still || reducedMotion.matches);
    drawMiddle(time, still || reducedMotion.matches);
    drawBottom(time, still || reducedMotion.matches);
    drawReplacementLabels();
  }

  const shouldAnimate = () => pageVisible && stageVisible && !reducedMotion.matches;

  const tick = (timestamp) => {
    animationFrame = 0;
    if (!shouldAnimate()) return;
    const interval = mobile ? 1000 / 30 : 1000 / 60;
    if (timestamp - lastFrameTime >= interval - 1) {
      draw(timestamp * 0.001);
      lastFrameTime = timestamp;
    }
    animationFrame = requestAnimationFrame(tick);
  };

  const syncAnimation = () => {
    if (shouldAnimate()) {
      if (!animationFrame) animationFrame = requestAnimationFrame(tick);
    } else {
      if (animationFrame) cancelAnimationFrame(animationFrame);
      animationFrame = 0;
      draw(performance.now() * 0.001, true);
    }
  };

  const setActiveLayer = (layer = "default") => {
    activeLayer = layer;
    stage.dataset.activeLayer = layer;
    if (explore) explore.dataset.activeLayer = layer;
    controls.forEach((control) => {
      const active = control.dataset.ecmlLayer === layer;
      control.classList.toggle("is-layer-active", active);
      if (control.classList.contains("cube-research-card")) {
        control.setAttribute("aria-current", active ? "true" : "false");
      }
    });
    draw(performance.now() * 0.001, reducedMotion.matches || !stageVisible);
  };

  const restoreLayer = () => {
    requestAnimationFrame(() => {
      const focused = document.activeElement?.closest?.("[data-ecml-layer]");
      const hovered = controls.find((control) => control.matches(":hover"));
      setActiveLayer(focused?.dataset.ecmlLayer || hovered?.dataset.ecmlLayer || "default");
    });
  };

  controls.forEach((control) => {
    const activate = () => setActiveLayer(control.dataset.ecmlLayer);
    control.addEventListener("focus", activate);
    control.addEventListener("blur", restoreLayer);
    control.addEventListener("pointerenter", activate);
    control.addEventListener("pointerleave", restoreLayer);
  });

  document.addEventListener("visibilitychange", () => {
    pageVisible = !document.hidden;
    syncAnimation();
  });
  reducedMotion.addEventListener?.("change", syncAnimation);

  const resizeObserver = new ResizeObserver(updateMapping);
  resizeObserver.observe(stage);
  const intersectionObserver = new IntersectionObserver((entries) => {
    stageVisible = entries.some((entry) => entry.isIntersecting);
    syncAnimation();
  }, { threshold: 0.01 });
  intersectionObserver.observe(stage);

  let resizeFrame = 0;
  const handleViewportResize = () => {
    if (resizeFrame) cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(() => {
      resizeFrame = 0;
      updateMapping();
    });
  };
  window.addEventListener("resize", handleViewportResize, { passive: true });
  window.visualViewport?.addEventListener("resize", handleViewportResize, { passive: true });

  image.addEventListener("load", updateMapping, { once: true });
  if (image.complete) updateMapping();
  setActiveLayer("default");
  syncAnimation();

  window.addEventListener("pageshow", () => {
    pageVisible = !document.hidden;
    updateMapping();
    syncAnimation();
  });

  window.addEventListener("pagehide", (event) => {
    if (animationFrame) cancelAnimationFrame(animationFrame);
    animationFrame = 0;
    if (!event.persisted) {
      resizeObserver.disconnect();
      intersectionObserver.disconnect();
      window.removeEventListener("resize", handleViewportResize);
      window.visualViewport?.removeEventListener("resize", handleViewportResize);
    }
  });
})();
