using System;
using System.Diagnostics;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

namespace AutoClickerPro
{
    public partial class Form1 : Form
    {
        #region Win32 API
        [DllImport("user32.dll")]
        private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

        [DllImport("user32.dll")]
        private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

        [DllImport("user32.dll")]
        private static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);

        [DllImport("user32.dll")]
        private static extern bool GetCursorPos(out POINT lpPoint);

        [DllImport("user32.dll")]
        private static extern bool SetCursorPos(int x, int y);

        [DllImport("winmm.dll", EntryPoint = "timeBeginPeriod")]
        private static extern uint timeBeginPeriod(uint uMilliseconds);

        [DllImport("winmm.dll", EntryPoint = "timeEndPeriod")]
        private static extern uint timeEndPeriod(uint uMilliseconds);

        [StructLayout(LayoutKind.Sequential)]
        public struct POINT
        {
            public int X;
            public int Y;
        }

        private const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
        private const uint MOUSEEVENTF_LEFTUP = 0x0004;
        private const uint MOUSEEVENTF_RIGHTDOWN = 0x0008;
        private const uint MOUSEEVENTF_RIGHTUP = 0x0010;
        private const uint MOUSEEVENTF_MIDDLEDOWN = 0x0020;
        private const uint MOUSEEVENTF_MIDDLEUP = 0x0040;

        private const int HOTKEY_ID_TOGGLE = 9001;
        private const int HOTKEY_ID_PICK = 9002;
        private const int WM_HOTKEY = 0x0312;
        #endregion

        #region Theme Colors
        private readonly Color BgMain = Color.FromArgb(24, 24, 37);
        private readonly Color BgCard = Color.FromArgb(30, 30, 46);
        private readonly Color BgInput = Color.FromArgb(17, 17, 27);
        private readonly Color BorderColor = Color.FromArgb(49, 50, 68);
        private readonly Color TextMain = Color.FromArgb(205, 214, 244);
        private readonly Color TextMuted = Color.FromArgb(166, 173, 200);
        private readonly Color AccentGreen = Color.FromArgb(166, 227, 161);
        private readonly Color AccentRed = Color.FromArgb(243, 139, 168);
        private readonly Color AccentBlue = Color.FromArgb(137, 180, 250);
        private readonly Color AccentPeach = Color.FromArgb(250, 179, 135);
        private readonly Color AccentYellow = Color.FromArgb(249, 226, 175);
        #endregion

        #region Controls
        private Label lblClicks = null!;
        private Label lblCps = null!;
        private Label lblStatus = null!;
        private Label lblLiveCursor = null!;
        private Label lblPickHint = null!;
        private Button btnStart = null!;
        private Button btnStop = null!;
        private Button btnPickCoord = null!;

        private NumericUpDown numHours = null!;
        private NumericUpDown numMins = null!;
        private NumericUpDown numSecs = null!;
        private NumericUpDown numMs = null!;
        private CheckBox chkJitter = null!;
        private NumericUpDown numJitter = null!;

        private RadioButton rbLeft = null!;
        private RadioButton rbRight = null!;
        private RadioButton rbMiddle = null!;

        private RadioButton rbSingle = null!;
        private RadioButton rbDouble = null!;
        private RadioButton rbTriple = null!;
        private RadioButton rbHold = null!;

        private RadioButton rbCurrentLoc = null!;
        private RadioButton rbFixedLoc = null!;
        private NumericUpDown numFixedX = null!;
        private NumericUpDown numFixedY = null!;

        private RadioButton rbInfinite = null!;
        private RadioButton rbCount = null!;
        private NumericUpDown numRepeatCount = null!;

        private ComboBox cboHotkey = null!;
        private CheckBox chkAlwaysOnTop = null!;

        private System.Windows.Forms.Timer timerLive = null!;
        #endregion

        #region State
        private bool isRunning = false;
        private Thread? workerThread;
        private readonly CancellationTokenSource cancelSource = new();
        private long totalClicks = 0;
        private long sessionClicks = 0;
        private double currentCps = 0.0;
        private readonly Stopwatch sw = new();
        private bool isHolding = false;
        private readonly Random rng = new();
        #endregion

        public Form1()
        {
            InitializeComponent();
            SetupCustomUI();
            RegisterHotkeys();

            timerLive = new System.Windows.Forms.Timer { Interval = 150 };
            timerLive.Tick += (s, e) =>
            {
                if (GetCursorPos(out POINT pt))
                {
                    lblLiveCursor.Text = $"Con trỏ: X={pt.X} | Y={pt.Y}";
                }
            };
            timerLive.Start();
        }

        private void SetupCustomUI()
        {
            this.Text = "Auto Clicker Pro (.NET 10) - Siêu Mượt, 0% CPU";
            this.Size = new Size(660, 560);
            this.MinimumSize = new Size(640, 520);
            this.BackColor = BgMain;
            this.ForeColor = TextMain;
            this.Font = new Font("Segoe UI", 9F, FontStyle.Regular);
            this.StartPosition = FormStartPosition.CenterScreen;

            // 1. TOP CONTAINER
            Panel topPanel = new Panel
            {
                Dock = DockStyle.Top,
                Height = 110,
                Padding = new Padding(12, 8, 12, 4),
                BackColor = BgMain
            };
            this.Controls.Add(topPanel);

            // Title & Stats row
            Panel titleRow = new Panel { Dock = DockStyle.Top, Height = 36, BackColor = BgMain };
            topPanel.Controls.Add(titleRow);

            Label titleLbl = new Label
            {
                Text = "⚡ AUTO CLICKER PRO",
                Font = new Font("Segoe UI", 12F, FontStyle.Bold),
                ForeColor = TextMain,
                AutoSize = true,
                Location = new Point(0, 4)
            };
            titleRow.Controls.Add(titleLbl);

            lblStatus = new Label
            {
                Text = "⏹ ĐÃ DỪNG",
                Font = new Font("Segoe UI", 9F, FontStyle.Bold),
                ForeColor = AccentRed,
                BackColor = Color.FromArgb(49, 50, 68),
                Padding = new Padding(10, 4, 10, 4),
                AutoSize = true,
                Dock = DockStyle.Right
            };
            titleRow.Controls.Add(lblStatus);

            lblCps = new Label
            {
                Text = "0.0 CPS",
                Font = new Font("Segoe UI", 9F, FontStyle.Bold),
                ForeColor = AccentYellow,
                BackColor = BgInput,
                Padding = new Padding(8, 4, 8, 4),
                AutoSize = true,
                Dock = DockStyle.Right
            };
            titleRow.Controls.Add(lblCps);

            lblClicks = new Label
            {
                Text = "Đã click: 0",
                Font = new Font("Segoe UI", 9F, FontStyle.Bold),
                ForeColor = AccentGreen,
                BackColor = BgInput,
                Padding = new Padding(8, 4, 8, 4),
                AutoSize = true,
                Dock = DockStyle.Right
            };
            titleRow.Controls.Add(lblClicks);

            // Action Buttons
            Panel btnPanel = new Panel { Dock = DockStyle.Bottom, Height = 54, BackColor = BgCard, Padding = new Padding(4) };
            topPanel.Controls.Add(btnPanel);

            btnStart = new Button
            {
                Text = "▶ BẮT ĐẦU CHẠY (Phím F6)",
                Font = new Font("Segoe UI", 11F, FontStyle.Bold),
                BackColor = Color.FromArgb(27, 77, 62),
                ForeColor = AccentGreen,
                FlatStyle = FlatStyle.Flat,
                Dock = DockStyle.Left,
                Width = 310,
                Cursor = Cursors.Hand
            };
            btnStart.FlatAppearance.BorderSize = 0;
            btnStart.Click += (s, e) => StartClicking();
            btnPanel.Controls.Add(btnStart);

            btnStop = new Button
            {
                Text = "⏹ DỪNG LẠI (Phím F6)",
                Font = new Font("Segoe UI", 11F, FontStyle.Bold),
                BackColor = Color.FromArgb(74, 37, 48),
                ForeColor = AccentRed,
                FlatStyle = FlatStyle.Flat,
                Dock = DockStyle.Right,
                Width = 310,
                Cursor = Cursors.Hand,
                Enabled = false
            };
            btnStop.FlatAppearance.BorderSize = 0;
            btnStop.Click += (s, e) => StopClicking();
            btnPanel.Controls.Add(btnStop);

            // 2. BOTTOM TOOLBAR
            Panel botPanel = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 38,
                Padding = new Padding(12, 6, 12, 6),
                BackColor = BgInput
            };
            this.Controls.Add(botPanel);

            Label lblHk = new Label { Text = "Phím Bật/Tắt:", ForeColor = TextMain, AutoSize = true, Location = new Point(10, 9) };
            botPanel.Controls.Add(lblHk);

            cboHotkey = new ComboBox
            {
                DropDownStyle = ComboBoxStyle.DropDownList,
                Location = new Point(100, 6),
                Width = 65,
                BackColor = BgCard,
                ForeColor = TextMain
            };
            for (int i = 1; i <= 12; i++) cboHotkey.Items.Add($"F{i}");
            cboHotkey.SelectedItem = "F6";
            cboHotkey.SelectedIndexChanged += (s, e) => RegisterHotkeys();
            botPanel.Controls.Add(cboHotkey);

            chkAlwaysOnTop = new CheckBox
            {
                Text = "📌 Luôn nổi trên cùng",
                ForeColor = TextMain,
                AutoSize = true,
                Location = new Point(180, 8),
                Checked = true
            };
            chkAlwaysOnTop.CheckedChanged += (s, e) => { this.TopMost = chkAlwaysOnTop.Checked; };
            this.TopMost = true;
            botPanel.Controls.Add(chkAlwaysOnTop);

            Button btnReset = new Button
            {
                Text = "🔄 Reset đếm",
                BackColor = Color.FromArgb(49, 50, 68),
                ForeColor = TextMain,
                FlatStyle = FlatStyle.Flat,
                Location = new Point(340, 5),
                Size = new Size(90, 26),
                Cursor = Cursors.Hand
            };
            btnReset.FlatAppearance.BorderSize = 0;
            btnReset.Click += (s, e) =>
            {
                totalClicks = 0;
                sessionClicks = 0;
                lblClicks.Text = "Đã click: 0";
                lblCps.Text = "0.0 CPS";
            };
            botPanel.Controls.Add(btnReset);

            lblLiveCursor = new Label
            {
                Text = "Con trỏ: X=0 | Y=0",
                ForeColor = TextMuted,
                AutoSize = true,
                Dock = DockStyle.Right,
                TextAlign = ContentAlignment.MiddleRight
            };
            botPanel.Controls.Add(lblLiveCursor);

            // 3. MAIN DASHBOARD BODY (2 COLUMNS)
            TableLayoutPanel bodyGrid = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 1,
                Padding = new Padding(8, 2, 8, 2),
                BackColor = BgMain
            };
            bodyGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50F));
            bodyGrid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50F));
            this.Controls.Add(bodyGrid);
            bodyGrid.BringToFront();

            // LEFT COLUMN
            Panel leftCol = new Panel { Dock = DockStyle.Fill, BackColor = BgMain };
            bodyGrid.Controls.Add(leftCol, 0, 0);

            // Left Box 1: Interval
            GroupBox grpInterval = CreateGroupBox("⏱ THỜI GIAN CLICK (INTERVAL)", leftCol, 195);
            BuildIntervalBox(grpInterval);

            // Left Box 2: Repeat
            GroupBox grpRepeat = CreateGroupBox("🔁 SỐ LẦN LẶP (REPEAT)", leftCol, 150);
            BuildRepeatBox(grpRepeat);

            // RIGHT COLUMN
            Panel rightCol = new Panel { Dock = DockStyle.Fill, BackColor = BgMain };
            bodyGrid.Controls.Add(rightCol, 1, 0);

            // Right Box 1: Mouse Options
            GroupBox grpOptions = CreateGroupBox("🖱 TÙY CHỌN CHUỘT (OPTIONS)", rightCol, 195);
            BuildMouseOptionsBox(grpOptions);

            // Right Box 2: Location
            GroupBox grpLocation = CreateGroupBox("📍 VỊ TRÍ CON TRỎ (LOCATION)", rightCol, 150);
            BuildLocationBox(grpLocation);
        }

        private GroupBox CreateGroupBox(string title, Panel parent, int height)
        {
            GroupBox gb = new GroupBox
            {
                Text = title,
                ForeColor = AccentBlue,
                Font = new Font("Segoe UI", 9F, FontStyle.Bold),
                BackColor = BgCard,
                Dock = DockStyle.Top,
                Height = height,
                Padding = new Padding(8)
            };
            parent.Controls.Add(gb);
            return gb;
        }

        private void BuildIntervalBox(GroupBox gb)
        {
            Label lblH = new Label { Text = "Giờ:", ForeColor = TextMuted, Location = new Point(12, 24), AutoSize = true, Font = new Font("Segoe UI", 8F) };
            numHours = CreateNum(0, 999, 0, new Point(12, 42), 60);

            Label lblM = new Label { Text = "Phút:", ForeColor = TextMuted, Location = new Point(80, 24), AutoSize = true, Font = new Font("Segoe UI", 8F) };
            numMins = CreateNum(0, 59, 0, new Point(80, 42), 60);

            Label lblS = new Label { Text = "Giây:", ForeColor = TextMuted, Location = new Point(148, 24), AutoSize = true, Font = new Font("Segoe UI", 8F) };
            numSecs = CreateNum(0, 59, 0, new Point(148, 42), 60);

            Label lblMs = new Label { Text = "Mili-giây (ms):", ForeColor = TextMuted, Location = new Point(216, 24), AutoSize = true, Font = new Font("Segoe UI", 8F) };
            numMs = CreateNum(1, 999999, 100, new Point(216, 42), 75);

            gb.Controls.AddRange(new Control[] { lblH, numHours, lblM, numMins, lblS, numSecs, lblMs, numMs });

            chkJitter = new CheckBox
            {
                Text = "Độ trễ ngẫu nhiên: ±",
                ForeColor = TextMain,
                Font = new Font("Segoe UI", 8.5F),
                Location = new Point(12, 85),
                AutoSize = true
            };
            numJitter = CreateNum(0, 5000, 15, new Point(165, 83), 60);
            Label lblJitMs = new Label { Text = "ms (chống ban)", ForeColor = TextMuted, Location = new Point(230, 85), AutoSize = true, Font = new Font("Segoe UI", 8F) };

            gb.Controls.AddRange(new Control[] { chkJitter, numJitter, lblJitMs });
        }

        private void BuildRepeatBox(GroupBox gb)
        {
            rbInfinite = new RadioButton
            {
                Text = "Lặp vô tận (cho đến khi bấm Dừng)",
                ForeColor = TextMain,
                Font = new Font("Segoe UI", 8.5F),
                Location = new Point(12, 25),
                AutoSize = true,
                Checked = true
            };

            rbCount = new RadioButton
            {
                Text = "Lặp cố định:",
                ForeColor = TextMain,
                Font = new Font("Segoe UI", 8.5F),
                Location = new Point(12, 55),
                AutoSize = true
            };
            numRepeatCount = CreateNum(1, 9999999, 100, new Point(110, 54), 80);
            Label lblTimes = new Label { Text = "lần", ForeColor = TextMuted, Location = new Point(195, 56), AutoSize = true, Font = new Font("Segoe UI", 8.5F) };

            gb.Controls.AddRange(new Control[] { rbInfinite, rbCount, numRepeatCount, lblTimes });
        }

        private void BuildMouseOptionsBox(GroupBox gb)
        {
            Label lblBtn = new Label { Text = "Phím chuột:", ForeColor = TextMuted, Location = new Point(12, 22), AutoSize = true, Font = new Font("Segoe UI", 8F) };
            rbLeft = new RadioButton { Text = "Trái", ForeColor = TextMain, Location = new Point(12, 40), AutoSize = true, Checked = true, Font = new Font("Segoe UI", 8.5F) };
            rbRight = new RadioButton { Text = "Phải", ForeColor = TextMain, Location = new Point(70, 40), AutoSize = true, Font = new Font("Segoe UI", 8.5F) };
            rbMiddle = new RadioButton { Text = "Giữa", ForeColor = TextMain, Location = new Point(130, 40), AutoSize = true, Font = new Font("Segoe UI", 8.5F) };

            Label lblType = new Label { Text = "Kiểu click:", ForeColor = TextMuted, Location = new Point(12, 72), AutoSize = true, Font = new Font("Segoe UI", 8F) };
            rbSingle = new RadioButton { Text = "Click đơn", ForeColor = TextMain, Location = new Point(12, 90), AutoSize = true, Checked = true, Font = new Font("Segoe UI", 8.5F) };
            rbDouble = new RadioButton { Text = "Click đúp", ForeColor = TextMain, Location = new Point(100, 90), AutoSize = true, Font = new Font("Segoe UI", 8.5F) };
            rbTriple = new RadioButton { Text = "3 lần", ForeColor = TextMain, Location = new Point(180, 90), AutoSize = true, Font = new Font("Segoe UI", 8.5F) };
            rbHold = new RadioButton { Text = "Giữ chuột (Hold)", ForeColor = TextMain, Location = new Point(12, 118), AutoSize = true, Font = new Font("Segoe UI", 8.5F) };

            gb.Controls.AddRange(new Control[] { lblBtn, rbLeft, rbRight, rbMiddle, lblType, rbSingle, rbDouble, rbTriple, rbHold });
        }

        private void BuildLocationBox(GroupBox gb)
        {
            rbCurrentLoc = new RadioButton
            {
                Text = "Tại vị trí chuột hiện tại",
                ForeColor = TextMain,
                Font = new Font("Segoe UI", 8.5F),
                Location = new Point(12, 22),
                AutoSize = true,
                Checked = true
            };

            rbFixedLoc = new RadioButton
            {
                Text = "Tọa độ cố định:",
                ForeColor = TextMain,
                Font = new Font("Segoe UI", 8.5F),
                Location = new Point(12, 48),
                AutoSize = true
            };

            Label lblX = new Label { Text = "X:", ForeColor = TextMuted, Location = new Point(120, 50), AutoSize = true, Font = new Font("Segoe UI", 8F) };
            numFixedX = CreateNum(0, 10000, 500, new Point(135, 48), 50);

            Label lblY = new Label { Text = "Y:", ForeColor = TextMuted, Location = new Point(190, 50), AutoSize = true, Font = new Font("Segoe UI", 8F) };
            numFixedY = CreateNum(0, 10000, 500, new Point(205, 48), 50);

            btnPickCoord = new Button
            {
                Text = "📍 Lấy [F7]",
                BackColor = Color.FromArgb(49, 50, 68),
                ForeColor = AccentPeach,
                FlatStyle = FlatStyle.Flat,
                Location = new Point(260, 46),
                Size = new Size(50, 25),
                Font = new Font("Segoe UI", 8F, FontStyle.Bold),
                Cursor = Cursors.Hand
            };
            btnPickCoord.FlatAppearance.BorderSize = 0;
            btnPickCoord.Click += (s, e) => CaptureCursorPosition();

            lblPickHint = new Label
            {
                Text = "",
                ForeColor = AccentPeach,
                Font = new Font("Segoe UI", 8F, FontStyle.Italic),
                Location = new Point(12, 80),
                AutoSize = true
            };

            gb.Controls.AddRange(new Control[] { rbCurrentLoc, rbFixedLoc, lblX, numFixedX, lblY, numFixedY, btnPickCoord, lblPickHint });
        }

        private NumericUpDown CreateNum(decimal min, decimal max, decimal val, Point loc, int width)
        {
            return new NumericUpDown
            {
                Minimum = min,
                Maximum = max,
                Value = val,
                Location = loc,
                Width = width,
                BackColor = BgInput,
                ForeColor = TextMain,
                Font = new Font("Segoe UI", 9F, FontStyle.Bold),
                TextAlign = HorizontalAlignment.Center
            };
        }

        #region Hotkey Handling (Native Win32 RegisterHotKey - 0% CPU)
        private void RegisterHotkeys()
        {
            UnregisterHotKey(this.Handle, HOTKEY_ID_TOGGLE);
            UnregisterHotKey(this.Handle, HOTKEY_ID_PICK);

            string keyName = cboHotkey.SelectedItem?.ToString() ?? "F6";
            if (Enum.TryParse<Keys>(keyName, out Keys vkToggle))
            {
                RegisterHotKey(this.Handle, HOTKEY_ID_TOGGLE, 0, (uint)vkToggle);
            }

            RegisterHotKey(this.Handle, HOTKEY_ID_PICK, 0, (uint)Keys.F7);

            btnStart.Text = $"▶ BẮT ĐẦU CHẠY (Phím {keyName})";
            btnStop.Text = $"⏹ DỪNG LẠI (Phím {keyName})";
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == WM_HOTKEY)
            {
                int id = m.WParam.ToInt32();
                if (id == HOTKEY_ID_TOGGLE)
                {
                    ToggleClicker();
                }
                else if (id == HOTKEY_ID_PICK)
                {
                    CaptureCursorPosition();
                }
            }
            base.WndProc(ref m);
        }

        private void CaptureCursorPosition()
        {
            if (GetCursorPos(out POINT pt))
            {
                numFixedX.Value = pt.X;
                numFixedY.Value = pt.Y;
                rbFixedLoc.Checked = true;
                lblPickHint.Text = $"✓ Đã lưu: X={pt.X}, Y={pt.Y}";
            }
        }
        #endregion

        #region Clicker Engine
        public void ToggleClicker()
        {
            if (isRunning) StopClicking();
            else StartClicking();
        }

        public void StartClicking()
        {
            if (isRunning) return;

            isRunning = true;
            sessionClicks = 0;
            sw.Restart();

            btnStart.Enabled = false;
            btnStart.BackColor = Color.FromArgb(20, 45, 36);

            btnStop.Enabled = true;
            btnStop.BackColor = Color.FromArgb(166, 52, 70);

            lblStatus.Text = "▶ ĐANG CHẠY";
            lblStatus.ForeColor = AccentGreen;
            lblStatus.BackColor = Color.FromArgb(30, 58, 47);

            // Read settings
            long intervalMs = (long)((numHours.Value * 3600 + numMins.Value * 60 + numSecs.Value) * 1000 + numMs.Value);
            if (intervalMs < 1) intervalMs = 1;

            bool useJitter = chkJitter.Checked;
            int jitterMs = (int)numJitter.Value;

            bool isRight = rbRight.Checked;
            bool isMiddle = rbMiddle.Checked;
            uint downFlag = isRight ? MOUSEEVENTF_RIGHTDOWN : (isMiddle ? MOUSEEVENTF_MIDDLEDOWN : MOUSEEVENTF_LEFTDOWN);
            uint upFlag = isRight ? MOUSEEVENTF_RIGHTUP : (isMiddle ? MOUSEEVENTF_MIDDLEUP : MOUSEEVENTF_LEFTUP);

            bool isDouble = rbDouble.Checked;
            bool isTriple = rbTriple.Checked;
            bool isHold = rbHold.Checked;

            bool isFixed = rbFixedLoc.Checked;
            int fixX = (int)numFixedX.Value;
            int fixY = (int)numFixedY.Value;

            bool isCount = rbCount.Checked;
            long targetCount = (long)numRepeatCount.Value;

            workerThread = new Thread(() =>
            {
                timeBeginPeriod(1);
                long lastUiUpdate = 0;

                try
                {
                    while (isRunning)
                    {
                        if (isFixed) SetCursorPos(fixX, fixY);

                        if (isHold)
                        {
                            if (!isHolding)
                            {
                                mouse_event(downFlag, 0, 0, 0, UIntPtr.Zero);
                                isHolding = true;
                            }
                        }
                        else if (isDouble)
                        {
                            mouse_event(downFlag, 0, 0, 0, UIntPtr.Zero);
                            Thread.Sleep(1);
                            mouse_event(upFlag, 0, 0, 0, UIntPtr.Zero);
                            Thread.Sleep(30);
                            mouse_event(downFlag, 0, 0, 0, UIntPtr.Zero);
                            Thread.Sleep(1);
                            mouse_event(upFlag, 0, 0, 0, UIntPtr.Zero);
                        }
                        else if (isTriple)
                        {
                            for (int i = 0; i < 3; i++)
                            {
                                mouse_event(downFlag, 0, 0, 0, UIntPtr.Zero);
                                Thread.Sleep(1);
                                mouse_event(upFlag, 0, 0, 0, UIntPtr.Zero);
                                if (i < 2) Thread.Sleep(30);
                            }
                        }
                        else // Single
                        {
                            mouse_event(downFlag, 0, 0, 0, UIntPtr.Zero);
                            Thread.Sleep(1);
                            mouse_event(upFlag, 0, 0, 0, UIntPtr.Zero);
                        }

                        totalClicks++;
                        sessionClicks++;

                        long elapsedMs = sw.ElapsedMilliseconds;
                        currentCps = elapsedMs > 0 ? (sessionClicks * 1000.0) / elapsedMs : 0;

                        // Throttle UI update to max 10 FPS
                        if (elapsedMs - lastUiUpdate >= 100 || (isCount && sessionClicks >= targetCount))
                        {
                            lastUiUpdate = elapsedMs;
                            long curTotal = totalClicks;
                            double curCps = currentCps;
                            this.BeginInvoke(new Action(() =>
                            {
                                lblClicks.Text = $"Đã click: {curTotal:N0}";
                                lblCps.Text = $"{curCps:F1} CPS";
                            }));
                        }

                        if (isCount && sessionClicks >= targetCount) break;

                        // Delay
                        long currentDelay = intervalMs;
                        if (useJitter && jitterMs > 0)
                        {
                            int offset = rng.Next(-jitterMs, jitterMs + 1);
                            currentDelay = Math.Max(1, currentDelay + offset);
                        }

                        if (currentDelay > 0)
                        {
                            Thread.Sleep((int)currentDelay);
                        }
                    }
                }
                finally
                {
                    if (isHolding)
                    {
                        mouse_event(upFlag, 0, 0, 0, UIntPtr.Zero);
                        isHolding = false;
                    }

                    timeEndPeriod(1);

                    this.BeginInvoke(new Action(() =>
                    {
                        StopClicking();
                    }));
                }
            })
            {
                IsBackground = true,
                Priority = ThreadPriority.Highest
            };

            workerThread.Start();
        }

        public void StopClicking()
        {
            if (!isRunning) return;

            isRunning = false;

            btnStart.Enabled = true;
            btnStart.BackColor = Color.FromArgb(27, 77, 62);

            btnStop.Enabled = false;
            btnStop.BackColor = Color.FromArgb(74, 37, 48);

            lblStatus.Text = "⏹ ĐÃ DỪNG";
            lblStatus.ForeColor = AccentRed;
            lblStatus.BackColor = Color.FromArgb(49, 50, 68);
        }
        #endregion

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            isRunning = false;
            UnregisterHotKey(this.Handle, HOTKEY_ID_TOGGLE);
            UnregisterHotKey(this.Handle, HOTKEY_ID_PICK);
            timerLive.Stop();
            base.OnFormClosing(e);
        }
    }
}
